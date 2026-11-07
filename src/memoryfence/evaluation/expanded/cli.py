"""CLI operations for the versioned Expanded Study."""

import argparse
import json
import lzma
import shutil
import tempfile
import zipfile
from pathlib import Path

from memoryfence.domain.errors import DomainValidationError

from .dataset import load
from .report import summarize
from .runner import execute


def export(directory: Path, output: Path) -> None:
    if output.exists() or directory.resolve() in output.resolve().parents:
        raise DomainValidationError("export must be new and outside the run directory")
    with tempfile.TemporaryDirectory(prefix="mf-expanded-export-") as temp:
        intermediate = Path(temp) / "raw.zip"
        with zipfile.ZipFile(intermediate, "x", compression=zipfile.ZIP_STORED) as archive:
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    archive.write(path, str(path.relative_to(directory)))
        with intermediate.open("rb") as source, lzma.open(output, "xb", preset=6) as target:
            shutil.copyfileobj(source, target)


def dispatch(args: argparse.Namespace) -> int:
    if args.expanded_command == "validate":
        benchmark = load(args.dataset)
        print(
            json.dumps(
                {
                    "version": benchmark.version,
                    "cases": len(benchmark.scenarios),
                    "families": len({s.family for s in benchmark.scenarios}),
                    "model_calls": 0,
                }
            )
        )
    elif args.expanded_command == "run":
        execute(args.dataset, args.directory, args.split)
        result = summarize(args.directory)
        (args.directory / "summary.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        print(
            json.dumps(
                {k: v for k, v in result.items() if k not in {"groups", "paired_family_deltas"}}
            )
        )
    elif args.expanded_command == "summarize":
        print(json.dumps(summarize(args.directory), indent=2, sort_keys=True))
    else:
        export(args.directory, args.output)
        print(str(args.output))
    return 0
