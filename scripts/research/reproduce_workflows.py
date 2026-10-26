"""Exercise offline researcher workflows in a new directory; no model calls."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=False)
    commands: list[list[str]] = [
        ["--help"],
        ["demo", "--directory", str(args.directory / "demo")],
        ["benchmark", "validate"],
        ["benchmark", "list"],
    ]
    for fidelity in ("LF1.0", "LF0.5"):
        for policy in ("DS0", "DS1", "DS3"):
            for defense in ("DF0", "DF2"):
                command = [
                    "benchmark",
                    "run",
                    "--scenario",
                    "post-deletion",
                    "--directory",
                    str(args.directory / f"{fidelity}-{policy}-{defense}"),
                    "--fidelity",
                    fidelity,
                    "--policy",
                    policy,
                    "--defense",
                    defense,
                ]
                if defense == "DF2":
                    command += ["--retrieval", "exclude"]
                commands.append(command)
    original = args.directory / "LF1.0-DS0-DF0"
    commands += [
        ["benchmark", "inspect", "--directory", str(original)],
        ["benchmark", "export", "--directory", str(original)],
        [
            "benchmark",
            "replay",
            "--directory",
            str(original),
            "--into",
            str(args.directory / "replay"),
        ],
        ["experiment", "smoke", "--directory", str(args.directory / "experiment")],
    ]
    for name in ("status", "audit", "verify", "summarize", "export"):
        commands.append(["experiment", name, "--directory", str(args.directory / "experiment")])
    records = []
    for index, command in enumerate(commands):
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "memoryfence", *command],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        record = {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        records.append(record)
        (args.directory / "workflow-results.json").write_text(json.dumps(records, indent=2) + "\n")
        print(f"{index + 1}/{len(commands)} passed: {' '.join(command[:2])}")


if __name__ == "__main__":
    main()
