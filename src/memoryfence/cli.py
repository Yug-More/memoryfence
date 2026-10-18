"""Command line for the offline demo and the scripted benchmark."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from memoryfence.benchmark.catalog import list_scenarios, validate_catalog
from memoryfence.benchmark.result import canonical_outcome
from memoryfence.benchmark.runner import RESULT_NAME, load_events, load_result, replay, run_scenario
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import (
    DefenseId,
    DeletionPolicy,
    LineageFidelity,
    PolicySource,
    RetrievalVariant,
)
from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.serialization import canonical_json
from memoryfence.evaluation.config import load_config, smoke_config
from memoryfence.evaluation.report import write_summary
from memoryfence.evaluation.runner import audit, execute, export_json, load_records, preview, verify
from memoryfence.harness.episode import run_demo
from memoryfence.llm.ollama import doctor, list_models, smoke_call


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memoryfence")
    commands = parser.add_subparsers(dest="command", required=True)
    model = commands.add_parser("model", help="local Ollama checks")
    model_commands = model.add_subparsers(dest="model_command", required=True)
    for name in ("doctor", "list"):
        command = model_commands.add_parser(name)
        command.add_argument("--endpoint", default="http://127.0.0.1:11434")
    smoke_model = model_commands.add_parser("smoke")
    smoke_model.add_argument("--model", required=True)
    smoke_model.add_argument("--endpoint", default="http://127.0.0.1:11434")
    experiment = commands.add_parser("experiment", help="scripted experiment matrix")
    experiment_commands = experiment.add_subparsers(dest="experiment_command", required=True)
    for name in ("validate", "preview"):
        command = experiment_commands.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
    for name in ("run",):
        command = experiment_commands.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
        command.add_argument("--directory", type=Path, required=True)
    experiment_commands.add_parser("smoke").add_argument("--directory", type=Path, required=True)
    for name in ("status", "resume", "export", "summarize", "verify", "audit"):
        experiment_commands.add_parser(name).add_argument("--directory", type=Path, required=True)
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
    run.add_argument("--defense", choices=[item.value for item in DefenseId], default="DF0")
    run.add_argument("--retrieval", choices=[item.value for item in RetrievalVariant])
    run.add_argument(
        "--policy-source", choices=[item.value for item in PolicySource], default="generated"
    )
    run.add_argument("--oracle-tool", action="append", default=[])
    run.add_argument("--risk-threshold", type=int, default=1)
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
    if args.command == "model":
        return _model(args)
    if args.command == "experiment":
        return _experiment(args)
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
            defense=_defense_config(args),
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


def _model(args: argparse.Namespace) -> int:
    if args.model_command == "doctor":
        status, message = doctor(args.endpoint)
        sys.stdout.write(message + "\n")
        return status
    if args.model_command == "list":
        status, message = list_models(args.endpoint)
        sys.stdout.write(message + "\n")
        return status
    if args.model_command == "smoke":
        status, message = smoke_call(args.endpoint, args.model)
        sys.stdout.write(message + "\n")
        return status
    return 2


def _experiment(args: argparse.Namespace) -> int:
    if args.experiment_command == "validate":
        matrix = preview(load_config(args.config))
        sys.stdout.write(f"candidates {matrix.candidates} valid {matrix.valid_count}\n")
        for item in matrix.exclusions:
            sys.stdout.write(f"excluded {item.scenario_id} {item.reason}\n")
        return 0
    if args.experiment_command == "preview":
        matrix = preview(load_config(args.config))
        sys.stdout.write(canonical_json(json.loads(matrix.model_dump_json())) + "\n")
        return 0
    if args.experiment_command == "smoke":
        execute(smoke_config(), args.directory, resume=False)
        sys.stdout.write("smoke completed\n")
        return 0
    if args.experiment_command == "run":
        execute(load_config(args.config), args.directory, resume=False)
        sys.stdout.write("experiment completed\n")
        return 0
    if args.experiment_command == "resume":
        execute(load_config(args.directory / "config.json"), args.directory, resume=True)
        sys.stdout.write("experiment resumed\n")
        return 0
    if args.experiment_command == "status":
        records = load_records(args.directory)
        completed = sum(record.status == "completed" for record in records)
        sys.stdout.write(f"recorded {len(records)} completed {completed}\n")
        return 0
    if args.experiment_command == "export":
        sys.stdout.write(export_json(args.directory) + "\n")
        return 0
    if args.experiment_command == "summarize":
        path = write_summary(args.directory)
        sys.stdout.write(f"{path}\n")
        return 0
    if args.experiment_command == "audit":
        ok = audit(args.directory)
        sys.stdout.write(json.dumps({"manifest_ok": ok, "rerun": False}) + "\n")
        return 0 if ok else 1
    if args.experiment_command == "verify":
        scratch = args.directory / "_verify"
        if scratch.exists():
            raise DomainValidationError("remove _verify before verifying")
        same = verify(args.directory, scratch)
        sys.stdout.write(json.dumps({"equivalent": same}) + "\n")
        return 0 if same else 1
    return 2


def _defense_config(args: argparse.Namespace) -> DefenseConfiguration:
    tools = tuple(sorted(set(args.oracle_tool)))
    try:
        return DefenseConfiguration(
            defense=DefenseId(args.defense),
            retrieval_variant=None if args.retrieval is None else RetrievalVariant(args.retrieval),
            policy_source=PolicySource(args.policy_source),
            oracle_tools=tools,
            risk_threshold=args.risk_threshold,
        )
    except ValidationError as error:
        raise DomainValidationError("defense configuration is invalid") from error
