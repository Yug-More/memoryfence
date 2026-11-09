"""Machine-readable scenario validation and structural split boundaries."""

import hashlib
import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import TransformationType
from memoryfence.domain.errors import DomainValidationError
from memoryfence.provenance.graph import topological_order

CANARY = "relay@vendor.invalid"


class Fact(DomainModel):
    id: str
    value: str


class Source(DomainModel):
    key: str
    kind: Literal["document", "email", "repository_file", "knowledge_base", "tool_response"]
    facts: tuple[Fact, ...]


class Node(DomainModel):
    key: str
    parents: tuple[str, ...] = Field(min_length=1)
    transformation: TransformationType


class Scenario(DomainModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,127}$")
    family: str
    split: Literal["development", "evaluation"]
    control: Literal["attack_complete", "attack_marked", "attack_silent", "clean", "never_exposed"]
    seed: int = Field(ge=0)
    nominal_fidelity: Literal["LF1.0", "LF0.5"]
    marked: bool
    sources: tuple[Source, ...]
    nodes: tuple[Node, ...]
    delete_source: str
    target_fact: str
    query: str

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        keys = [s.key for s in self.sources] + [n.key for n in self.nodes]
        if len(keys) != len(set(keys)) or self.delete_source not in {s.key for s in self.sources}:
            raise ValueError("duplicate nodes or absent deletion source")
        facts = [f.id for s in self.sources for f in s.facts]
        if len(facts) != len(set(facts)) or self.target_fact not in facts:
            raise ValueError("duplicate fact or absent utility target")
        seen = {s.key for s in self.sources}
        for node in self.nodes:
            if len(node.parents) != len(set(node.parents)) or not set(node.parents) <= seen:
                raise ValueError("parents must exist once and precede their child")
            seen.add(node.key)
        topological_order({n.key: n.parents for n in self.nodes})
        target = next(s for s in self.sources if s.key == self.delete_source)
        if self.target_fact in {f.id for f in target.facts}:
            raise ValueError("utility target must be unrelated to deleted source")
        poisoned = any(CANARY in f.value for f in target.facts)
        if poisoned != (self.control != "clean"):
            raise ValueError("control and source annotation disagree")
        ancestors: dict[str, set[str]] = {s.key: {s.key} for s in self.sources}
        for n in self.nodes:
            ancestors[n.key] = set().union(*(ancestors[p] for p in n.parents))
        exposed = any(self.delete_source in ancestors[n.key] for n in self.nodes)
        if exposed == (self.control == "never_exposed"):
            raise ValueError("never-exposure annotation disagrees with graph")
        if self.marked != (self.control == "attack_marked"):
            raise ValueError("marked flag inconsistent with control")
        partial = self.control in {"attack_marked", "attack_silent"}
        if (self.nominal_fidelity == "LF0.5") != partial:
            raise ValueError("nominal fidelity inconsistent with control")
        return self


class Benchmark(DomainModel):
    version: Literal["expanded-v1"]
    classification: Literal["deterministic memory-system benchmark; zero model inference"]
    scenarios: tuple[Scenario, ...]

    @model_validator(mode="after")
    def validate_split(self) -> Self:
        if len({s.id for s in self.scenarios}) != len(self.scenarios):
            raise ValueError("scenario IDs must be unique")
        splits: dict[str, str] = {}
        signatures: dict[str, str] = {}
        for case in self.scenarios:
            if splits.setdefault(case.family, case.split) != case.split:
                raise ValueError("family leaks across splits")
            if case.control != "attack_complete":
                continue
            shape = json.dumps([(n.key, n.parents, n.transformation.value) for n in case.nodes])
            if shape in signatures and signatures[shape] != case.family:
                raise ValueError("duplicate graph/operation family signature")
            signatures[shape] = case.family
        if set(splits.values()) != {"development", "evaluation"}:
            raise ValueError("both grouped splits required")
        return self


def load(path: Path) -> Benchmark:
    try:
        return Benchmark.model_validate_json(path.read_text())
    except (ValueError, OSError) as error:
        raise DomainValidationError(f"invalid expanded benchmark: {error}") from error


def dataset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fact_text(facts: tuple[Fact, ...]) -> str:
    return json.dumps([f.model_dump() for f in facts], sort_keys=True)


def read_facts(text: str) -> tuple[Fact, ...]:
    data = json.loads(text)
    if not isinstance(data, list):
        raise DomainValidationError("expanded projection expects a fact list")
    return tuple(Fact.model_validate(f) for f in data)
