"""Versioned experiment configuration. Invalid combinations are rejected."""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import ConfigDict, Field, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity
from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.serialization import canonical_json, sha256_hex

SplitName = Literal["development", "evaluation"]
BlockName = Literal["custom", "smoke", "e3"]


class ExperimentConfig(DomainModel):
    """One planned comparison. ``max_runs`` is a hard stop, not a silent sample."""

    model_config = ConfigDict(frozen=True, strict=False, extra="forbid", validate_default=True)

    experiment_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    version: int = Field(ge=1)
    block: BlockName
    split: SplitName
    scenarios: tuple[str, ...] = Field(min_length=1)
    defenses: tuple[DefenseConfiguration, ...] = Field(min_length=1)
    deletion_policies: tuple[DeletionPolicy, ...] = Field(min_length=1)
    fidelities: tuple[LineageFidelity, ...] = Field(min_length=1)
    replicates: int = Field(default=1, ge=1, le=3)
    backend: Literal["scripted"] = "scripted"
    max_runs: int = Field(ge=1, le=64)

    @model_validator(mode="before")
    @classmethod
    def _json_shapes(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        for key in ("scenarios", "deletion_policies", "fidelities"):
            item = data.get(key)
            if isinstance(item, list):
                data[key] = tuple(item)
        defenses = data.get("defenses")
        if isinstance(defenses, list):
            data["defenses"] = tuple(
                item
                if isinstance(item, DefenseConfiguration)
                else DefenseConfiguration.model_validate(item, strict=False)
                for item in defenses
            )
        return data

    @model_validator(mode="after")
    def _scripted_limits(self) -> Self:
        if self.replicates != 1:
            raise ValueError("the scripted backend does not sample replicates")
        if len(self.scenarios) != len(set(self.scenarios)):
            raise ValueError("scenario ids must be unique")
        return self

    def fingerprint(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json")))


def load_config(path: Path) -> ExperimentConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ExperimentConfig.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise DomainValidationError("experiment configuration is invalid") from error


def smoke_config() -> ExperimentConfig:
    """One development scenario under ``DF0``. It is a mechanics check."""
    return ExperimentConfig(
        experiment_id="smoke",
        version=1,
        block="smoke",
        split="development",
        scenarios=("clean-note",),
        defenses=(DefenseConfiguration(),),
        deletion_policies=(DeletionPolicy.NO_DELETION,),
        fidelities=(LineageFidelity.LF1_0,),
        max_runs=1,
    )
