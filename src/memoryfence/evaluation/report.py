"""Summaries of a finished scripted experiment. These are not model findings."""

from pathlib import Path

from memoryfence.evaluation.hypotheses import hypothesis_links
from memoryfence.evaluation.metrics import StageCounts, StageRates, rates
from memoryfence.evaluation.runner import SUMMARY_NAME, RunRecord, load_records

_LEGIT = frozenset({"C-CLEAN", "C-LEGIT", "C-SELF"})


def write_summary(directory: Path) -> Path:
    records = load_records(directory)
    completed = [record for record in records if record.status == "completed"]
    invalid = [record for record in records if record.status != "completed"]
    counts = StageCounts(
        trials=len(completed),
        retrieved=sum(bool(record.retrieved) for record in completed),
        followed=sum(bool(record.followed) for record in completed),
        proposed=sum(bool(record.proposed) for record in completed),
        executed=sum(bool(record.executed) for record in completed),
        legitimate_trials=sum(record.control in _LEGIT for record in completed),
        legitimate_completed=sum(
            record.control in _LEGIT and bool(record.legitimate_task) for record in completed
        ),
        invalid=len(invalid),
    )
    summary = rates(counts)
    path = directory / SUMMARY_NAME
    path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    report = _markdown(records, counts, summary)
    (directory / "report.md").write_text(report, encoding="utf-8")
    return path


def _markdown(records: tuple[RunRecord, ...], counts: StageCounts, summary: StageRates) -> str:
    text = summary.executed
    lines = [
        "# Scripted experiment summary",
        "",
        "These counts come from the scripted backend. They are not language-model attack rates.",
        "",
        f"- Runs recorded: {len(records)}",
        f"- Completed: {counts.trials}",
        f"- Invalid or incomplete: {counts.invalid}",
        f"- S1 retrieved: {counts.retrieved}/{counts.trials}",
        f"- S2 followed: {counts.followed}/{counts.trials}",
        f"- S3 proposed: {counts.proposed}/{counts.trials}",
        f"- S4 executed: {counts.executed}/{counts.trials}",
        "",
        "## Uncertainty",
        "",
    ]
    if text.undefined or text.lower is None or text.upper is None:
        lines.append("S4 has no completed trials, so its Wilson interval is undefined.")
    else:
        lines.append(
            f"S4 Wilson 95% interval: {text.lower:.4f} to {text.upper:.4f} "
            f"({text.successes}/{text.trials})."
        )
    lines.extend(["", "## Hypothesis procedures", ""])
    for link in hypothesis_links():
        lines.append(f"- {link.hypothesis_id} ({link.status}): {link.note}")
    lines.append("")
    return "\n".join(lines)
