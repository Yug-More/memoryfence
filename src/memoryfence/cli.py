"""Command line for the offline demo and the scripted benchmark."""

import argparse
import json
import sys
from pathlib import Path

from memoryfence.benchmark.catalog import list_scenarios, validate_catalog
from memoryfence.benchmark.result import canonical_outcome
from memoryfence.benchmark.runner import RESULT_NAME, load_events, load_result, replay, run_scenario
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity
from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.serialization import canonical_json
from memoryfence.harness.episode import run_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memoryfence")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run the offline scripted collaborative episode")
    demo.add_argument("--directory", type=Path, required=True)
    benchmark = commands.add_parser("benchmark", help="scripted scenario benchmark")
    bench = benchmark.add_subparsers(dest="benchmark_command", required=True)
    bench.add_parser("list", help="list scenario ids")
    bench.add_parser("validate", help="validate the shipped fixtures")
    run = bench.add_parser("run", help="run one scenario")
    run.add_argument("--scenario", required=True)
    run.add_argument("--directory", type=Path, required=True)
    run.add_argument("--policy", choices=[item.value for item in DeletionPolicy])
    run.add_argument("--fidelity", choices=[item.value for item in LineageFidelity])
    run.add_argument("--marked", action="store_true")
    run.add_argument("--code-version", default="unspecified")
    again = bench.add_parser("replay", help="run a saved scenario again and compare")
    again.add_argument("--directory", type=Path, required=True)
    again.add_argument("--into", type=Path, required=True)
    again.add_argument("--code-version", default="unspecified")
    inspect = bench.add_parser("inspect", help="print a saved scripted result")
    inspect.add_argument("--directory", type=Path, required=True)
    export = bench.add_parser("export", help="print the result and event count")
    export.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except DomainValidationError as error:
        sys.stderr.write(f"{error}\n")
        return 2


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "demo":
        trace = run_demo(args.directory)
        payload = json.loads(trace.model_dump_json())
        if not isinstance(payload, dict):
            raise DomainValidationError("demo trace is not a JSON object")
        sys.stdout.write(canonical_json(payload) + "\n")
        return 0
    if args.command != "benchmark":
        return 2
    if args.benchmark_command == "list":
        for spec in list_scenarios():
            sys.stdout.write(f"{spec.id}\t{spec.family}\t{spec.version}\n")
        return 0
    if args.benchmark_command == "validate":
        validate_catalog()
        sys.stdout.write(f"valid {len(list_scenarios())}\n")
        return 0
    if args.benchmark_command == "run":
        result = run_scenario(
            args.scenario,
            args.directory,
            policy=None if args.policy is None else DeletionPolicy(args.policy),
            fidelity=None if args.fidelity is None else LineageFidelity(args.fidelity),
            marked=args.marked,
            code_version=args.code_version,
        )
        sys.stdout.write(canonical_json(json.loads(result.model_dump_json())) + "\n")
        return 0
    if args.benchmark_command == "replay":
        previous, fresh = replay(args.directory, args.into, code_version=args.code_version)
        same = canonical_outcome(previous) == canonical_outcome(fresh)
        sys.stdout.write(json.dumps({"equivalent": same}) + "\n")
        return 0 if same else 1
    if args.benchmark_command == "inspect":
        result = load_result(args.directory)
        sys.stdout.write(f"{result.scenario_id} {result.run_id} {RESULT_NAME}\n")
        return 0
    if args.benchmark_command == "export":
        result = load_result(args.directory)
        events = load_events(args.directory)
        sys.stdout.write(
            canonical_json(json.loads(result.model_dump_json())) + "\n" + f"events {len(events)}\n"
        )
        return 0
    return 2
