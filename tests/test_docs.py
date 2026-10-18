import re
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
RESEARCH = DOCS / "research"
OVERVIEW = DOCS / "architecture" / "overview.md"
PROTOCOL = RESEARCH / "experimental-protocol.md"

RESEARCH_QUESTION = (
    "Under what conditions can attacker-origin instructions persist in derived AI memories "
    "after transformations or original-source deletion, and how do deletion handling, "
    "provenance completeness, and defense mechanisms influence unauthorized downstream "
    "agent behavior?"
)

REQUIRED_DOCUMENTS = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CITATION.cff",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/development.md",
    "docs/roadmap.md",
    "docs/architecture/overview.md",
    "docs/architecture/decisions/ADR-0001-architecture.md",
    "docs/research/literature-review.md",
    "docs/research/problem-statement.md",
    "docs/research/threat-model.md",
    "docs/research/hypotheses.md",
    "docs/research/experimental-protocol.md",
    "docs/research/limitations.md",
]

REQUIRED_DIAGRAM_SECTIONS = [
    "High-level architecture",
    "Trust and visibility boundaries",
    "Source and memory lifecycle",
    "Transformation lineage",
    "Deletion and provenance handling",
    "Agent retrieval and authorization",
    "Experimental pipeline",
]

FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_LINK_TEXT = re.compile(r"\[([^\]]*)\]\([^)]*\)")
CONDITION_CODE = re.compile(r"\b(?:TT[0-9]|DS[0-9]|DF[0-9]|LF[0-9]\.[0-9]+|C-[A-Z]{2,})\b")


def markdown_files() -> list[Path]:
    files = [REPO_ROOT / name for name in ("README.md", "CONTRIBUTING.md", "SECURITY.md")]
    files += sorted(DOCS.rglob("*.md"))
    files += sorted((REPO_ROOT / ".github").rglob("*.md"))
    return files


def prose_lines(path: Path) -> list[str]:
    """Return the lines of a Markdown file that are outside fenced code blocks."""
    lines: list[str] = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


def github_slug(heading: str) -> str:
    text = INLINE_LINK_TEXT.sub(r"\1", heading).replace("`", "")
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: Counter[str] = Counter()
    result: set[str] = set()
    for line in prose_lines(path):
        match = HEADING.match(line)
        if not match:
            continue
        slug = github_slug(match.group(2))
        result.add(slug if seen[slug] == 0 else f"{slug}-{seen[slug]}")
        seen[slug] += 1
    return result


def relative_links(path: Path) -> list[str]:
    return [
        target
        for line in prose_lines(path)
        for target in LINK.findall(line)
        if not re.match(r"^[a-z][a-z0-9+.-]*:", target)
    ]


def sections(path: Path) -> dict[str, str]:
    """Map each level-2 heading (without its number) to the text beneath it."""
    result: dict[str, str] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = re.sub(r"^\d+\.\s*", "", line[3:].strip())
            result[current] = ""
        elif current is not None:
            result[current] += line + "\n"
    return result


@pytest.mark.parametrize("name", REQUIRED_DOCUMENTS)
def test_required_document_exists_and_is_not_empty(name: str) -> None:
    path = REPO_ROOT / name
    assert path.is_file(), f"missing {name}"
    assert path.read_text(encoding="utf-8").strip(), f"{name} is empty"


@pytest.mark.parametrize("path", markdown_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_relative_links_and_anchors_resolve(path: Path) -> None:
    broken: list[str] = []
    for target in relative_links(path):
        file_part, _, fragment = target.partition("#")
        destination = (path.parent / file_part).resolve() if file_part else path
        if not destination.exists():
            broken.append(f"{target} (no such file)")
        elif fragment and destination.suffix == ".md" and fragment not in anchors(destination):
            broken.append(f"{target} (no such heading)")
    assert not broken, f"broken links in {path.relative_to(REPO_ROOT)}: {broken}"


def test_github_slug_matches_github_heading_ids() -> None:
    assert github_slug("4.5 Deletion scenarios") == "45-deletion-scenarios"
    assert github_slug("[Xu2026] Memory Provenance Laundering (PPMF)") == (
        "xu2026-memory-provenance-laundering-ppmf"
    )
    assert github_slug("`DS4` re-derivation") == "ds4-re-derivation"


def test_research_question_is_stated_verbatim() -> None:
    for name in ("README.md", "docs/research/problem-statement.md"):
        text = " ".join((REPO_ROOT / name).read_text(encoding="utf-8").split())
        assert RESEARCH_QUESTION in text, f"research question not verbatim in {name}"


def test_condition_codes_are_defined_in_the_protocol() -> None:
    defined = set(CONDITION_CODE.findall(" ".join(prose_lines(PROTOCOL))))
    undefined = {
        f"{path.relative_to(REPO_ROOT)}: {code}"
        for path in markdown_files()
        for code in CONDITION_CODE.findall(" ".join(prose_lines(path)))
        if code not in defined
    }
    assert not undefined, f"condition codes not defined in the protocol: {sorted(undefined)}"


def test_protocol_defines_exactly_five_deletion_policies() -> None:
    policies = set(re.findall(r"\bDS[0-9]\b", PROTOCOL.read_text(encoding="utf-8")))
    assert policies == {"DS0", "DS1", "DS2", "DS3", "DS4"}


def test_protocol_defines_three_provenance_conditions() -> None:
    section = sections(PROTOCOL)["Independent variables"]
    for condition in ("Complete", "Partially missing", "Absent"):
        assert f"| {condition} recorded provenance |" in section


def test_protocol_defines_four_separate_outcome_stages() -> None:
    section = sections(PROTOCOL)["Outcome measurement"]
    for stage in ("S1 Retrieved", "S2 Followed", "S3 Proposed", "S4 Executed"):
        assert f"| **{stage}** |" in section


@pytest.mark.parametrize("title", REQUIRED_DIAGRAM_SECTIONS)
def test_architecture_overview_contains_required_diagram(title: str) -> None:
    overview_sections = sections(OVERVIEW)
    assert title in overview_sections, f"missing section {title!r}"
    assert "```mermaid" in overview_sections[title], f"no Mermaid diagram under {title!r}"
