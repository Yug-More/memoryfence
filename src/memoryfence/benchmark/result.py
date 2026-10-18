"""Scripted benchmark results. These are not empirical model findings."""

from typing import Literal

from pydantic import JsonValue

from memoryfence.benchmark.score import StageRecord
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity, MissingnessMode
from memoryfence.domain.serialization import canonical_json


class BenchmarkResult(DomainModel):
    kind: Literal["scripted-benchmark"]
    scenario_id: str
    scenario_version: int
    family: str
    protocol_family: str | None
    control: str | None
    run_id: str
    seed: int
    code_version: str
    deletion_policy: DeletionPolicy
    fidelity: LineageFidelity
    defense: str = "DF0"
    retrieval_variant: str | None = None
    policy_source: str = "generated"
    oracle_tools: tuple[str, ...] = ()
    risk_threshold: int = 1
    missingness: MissingnessMode
    confirmatory: bool
    transformation_chain: tuple[str, ...]
    stages: StageRecord | None
    authorization_reason: str | None
    legitimate_task: bool
    failure_reason: str | None
    trace_path: str


def canonical_outcome(result: BenchmarkResult) -> str:
    """Compare runs without the directory path or the code revision string."""
    payload = result.model_dump(mode="json")
    payload.pop("trace_path", None)
    payload.pop("code_version", None)
    return canonical_json(payload)


def canonical_events(events: list[dict[str, JsonValue]]) -> str:
    """Drop retrieval latency, which is the only nondeterministic event field."""
    copied: list[JsonValue] = []
    for event in events:
        item = dict(event)
        details = item.get("details")
        if isinstance(details, dict) and "elapsed_us" in details:
            item["details"] = {key: value for key, value in details.items() if key != "elapsed_us"}
        copied.append(item)
    return canonical_json(copied)
