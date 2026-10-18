"""Command line. ``demo`` runs the offline scripted episode and prints a JSON trace."""

import argparse
import json
import sys
from pathlib import Path

from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.serialization import canonical_json
from memoryfence.harness.episode import run_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memoryfence")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run the offline scripted collaborative episode")
    demo.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command != "demo":
        return 2
    trace = run_demo(args.directory)
    payload = json.loads(trace.model_dump_json())
    if not isinstance(payload, dict):
        raise DomainValidationError("demo trace is not a JSON object")
    sys.stdout.write(canonical_json(payload) + "\n")
    return 0
