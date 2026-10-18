"""Public scenario inputs. Evaluator labels are not fields on these models."""

from typing import Literal, Self

from pydantic import Field, model_validator

from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import DeletionPolicy, LineageFidelity, TransformationType
from memoryfence.domain.memories import PromptVersion
from memoryfence.domain.tools import ToolName

OwnerName = Literal["avery", "blake"]
FAMILIES = frozenset("ABCDEFGH")
PROTOCOL_FAMILIES = frozenset({"SF1", "SF2", "SF3", "SF4", "SF5"})
CONTROLS = frozenset({"C-CLEAN", "C-RAW", "C-NULL", "C-PREDEL", "C-LEGIT", "C-SELF", "C-UCC"})


class ScenarioSource(DomainModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")
    owner: OwnerName
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)


class ScenarioTransform(DomainModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9-]{0,31}$")
    transformation: TransformationType
    parent_keys: tuple[str, ...] = Field(min_length=1)
    text: str = Field(min_length=1, max_length=4000)
    script_id: PromptVersion


class ScenarioAction(DomainModel):
    """One scripted victim step. The text is a fixture, not a model generation."""

    task: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1, max_length=4000)
    script_id: PromptVersion
    tool_name: ToolName | None = None
    arguments: tuple[tuple[str, str], ...] = ()


class ScenarioSpec(DomainModel):
    """What the harness may show a developer. It carries no attack-success predicate."""

    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    version: int = Field(ge=1)
    family: str
    protocol_family: str | None = None
    control: str | None = None
    description: str = Field(min_length=1, max_length=400)
    deletion_policy: DeletionPolicy
    fidelity: LineageFidelity
    seed: int = Field(ge=0, lt=2**63)
    deletion_source_key: str | None = None
    delete_before_transform: bool = False
    inject_timeout: bool = False
    sources: tuple[ScenarioSource, ...] = Field(min_length=1)
    transforms: tuple[ScenarioTransform, ...] = ()
    actions: tuple[ScenarioAction, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _structure_is_consistent(self) -> Self:
        if self.family not in FAMILIES:
            raise ValueError("family must be A through H")
        if self.protocol_family is not None and self.protocol_family not in PROTOCOL_FAMILIES:
            raise ValueError("protocol family must be SF1 through SF5")
        if self.control is not None and self.control not in CONTROLS:
            raise ValueError("unknown control code")
        keys = [source.key for source in self.sources]
        if len(keys) != len(set(keys)):
            raise ValueError("source keys must be unique")
        known = set(keys)
        for step in self.transforms:
            if step.key in known:
                raise ValueError(f"duplicate key {step.key}")
            missing = [key for key in step.parent_keys if key not in known]
            if missing:
                raise ValueError(f"unknown parent {missing[0]}")
            known.add(step.key)
        if (
            self.deletion_policy is not DeletionPolicy.NO_DELETION
            and self.deletion_source_key is None
        ):
            raise ValueError("a deletion policy needs a source key")
        if self.deletion_source_key is not None and self.deletion_source_key not in keys:
            raise ValueError("deletion source key is not a source")
        if self.delete_before_transform and self.deletion_policy is DeletionPolicy.NO_DELETION:
            raise ValueError("pre-deletion requires a deletion policy")
        return self
