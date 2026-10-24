"""Versioned experiment configuration. Invalid combinations are rejected."""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import ConfigDict, Field, JsonValue, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity
from memoryfence.domain.errors import DomainValidationError
from memoryfence.domain.serialization import canonical_json, sha256_hex
from memoryfence.llm.endpoint import require_loopback

SplitName = Literal["development", "evaluation"]
BlockName = Literal["custom", "smoke", "e3"]
BackendName = Literal["scripted", "ollama"]
_OMIT_WHEN_SCRIPTED = (
    "output_mode",
    "model_tag",
    "endpoint",
    "temperature",
    "num_ctx",
    "num_predict",
    "timeout_seconds",
    "max_model_calls",
    "prompt_template",
    "judge_version",
    "transformation_backend",
)


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
    backend: BackendName = "scripted"
    max_runs: int = Field(ge=1, le=64)
    model_tag: str | None = None
    endpoint: str = "http://127.0.0.1:11434"
    temperature: float = Field(default=0.0, ge=0, le=1)
    num_ctx: int = Field(default=2048, ge=256, le=8192)
    num_predict: int = Field(default=256, ge=16, le=1024)
    timeout_seconds: float = Field(default=30, ge=1, le=120)
    max_model_calls: int = Field(default=8, ge=1, le=32)
    output_mode: Literal["native", "json_schema"] = "native"
    prompt_template: Literal["agent-v1", "agent-v2-json-schema"] = "agent-v1"
    judge_version: Literal["rubric-v1"] = "rubric-v1"
    transformation_backend: Literal["scripted", "ollama"] = "scripted"

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
        if len(self.scenarios) != len(set(self.scenarios)):
            raise ValueError("scenario ids must be unique")
        if self.backend == "scripted":
            if self.output_mode != "native" or self.prompt_template != "agent-v1":
                raise ValueError("scripted experiments do not use a model output schema")
            if self.replicates != 1 or self.model_tag is not None:
                raise ValueError("the scripted backend does not sample replicates or a model")
            if self.transformation_backend != "scripted":
                raise ValueError("the scripted backend does not use a model transformation")
            return self
        if self.output_mode == "json_schema" and self.prompt_template != "agent-v2-json-schema":
            raise ValueError("json_schema requires agent-v2-json-schema")
        if self.output_mode == "native" and self.prompt_template != "agent-v1":
            raise ValueError("native output requires agent-v1")
        if self.output_mode == "json_schema" and self.transformation_backend != "scripted":
            raise ValueError("the schema pilot supports scripted transformations only")
        if self.model_tag is None:
            raise ValueError("an ollama experiment requires a model tag")
        try:
            require_loopback(self.endpoint)
        except DomainValidationError as error:
            raise ValueError("the model endpoint must be http on loopback") from error
        if self.transformation_backend == "ollama" and self.prompt_template != "agent-v1":
            raise ValueError("unknown prompt template")
        return self

    def stored_json(self) -> JsonValue:
        data = super().model_dump(mode="json")
        if isinstance(data, dict) and data.get("output_mode") == "native":
            data.pop("output_mode", None)
        if isinstance(data, dict) and data.get("backend") == "scripted":
            for key in _OMIT_WHEN_SCRIPTED:
                data.pop(key, None)
        return data

    def fingerprint(self) -> str:
        return sha256_hex(canonical_json(self.stored_json()))


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
