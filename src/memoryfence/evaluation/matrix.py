"""Inspectable run matrix. Exclusions are reported and are not silent omissions."""

from memoryfence.benchmark.catalog import list_scenarios, load_scenario
from memoryfence.benchmark.spec import ScenarioSpec
from memoryfence.domain.base import DomainModel
from memoryfence.domain.defenses import DefenseConfiguration
from memoryfence.domain.enums import DefenseId, DeletionPolicy, LineageFidelity, RetrievalVariant
from memoryfence.domain.errors import DomainValidationError
from memoryfence.evaluation.config import ExperimentConfig
from memoryfence.evaluation.heldout import load_heldout

_E3_DEFENSES = (
    DefenseConfiguration(),
    DefenseConfiguration(defense=DefenseId.PROMPT),
    DefenseConfiguration(defense=DefenseId.RETRIEVAL, retrieval_variant=RetrievalVariant.EXCLUDE),
    DefenseConfiguration(defense=DefenseId.ACTION),
    DefenseConfiguration(defense=DefenseId.COMBINED, retrieval_variant=RetrievalVariant.EXCLUDE),
    DefenseConfiguration(defense=DefenseId.LINEAGE),
)


class PlannedRun(DomainModel):
    ordinal: int
    scenario_id: str
    defense: DefenseConfiguration
    deletion_policy: DeletionPolicy
    fidelity: LineageFidelity
    seed: int


class Exclusion(DomainModel):
    scenario_id: str
    reason: str


class RunMatrix(DomainModel):
    candidates: int
    runs: tuple[PlannedRun, ...]
    exclusions: tuple[Exclusion, ...]

    @property
    def valid_count(self) -> int:
        return len(self.runs)


def build_matrix(config: ExperimentConfig) -> RunMatrix:
    scenarios = _scenarios_for(config)
    defenses = _E3_DEFENSES if config.block == "e3" else config.defenses
    policies = (
        (DeletionPolicy.NO_DELETION, DeletionPolicy.SOURCE_AND_PRIMARY)
        if config.block == "e3"
        else config.deletion_policies
    )
    fidelities = (LineageFidelity.LF1_0,) if config.block == "e3" else config.fidelities
    candidates = len(scenarios) * len(defenses) * len(policies) * len(fidelities)
    runs: list[PlannedRun] = []
    exclusions: list[Exclusion] = []
    for scenario_id in scenarios:
        spec = _load(config.split, scenario_id)
        for defense in defenses:
            for policy in policies:
                for fidelity in fidelities:
                    reason = _exclude(spec.deletion_source_key, policy, config.split, scenario_id)
                    if reason is not None:
                        exclusions.append(Exclusion(scenario_id=scenario_id, reason=reason))
                        continue
                    runs.append(
                        PlannedRun(
                            ordinal=len(runs) + 1,
                            scenario_id=scenario_id,
                            defense=defense,
                            deletion_policy=policy,
                            fidelity=fidelity,
                            seed=spec.seed,
                        )
                    )
    return RunMatrix(candidates=candidates, runs=tuple(runs), exclusions=tuple(exclusions))


def require_run_limit(config: ExperimentConfig, matrix: RunMatrix) -> None:
    """Refuse execution when the valid matrix is larger than the configured stop."""
    if matrix.valid_count > config.max_runs:
        raise DomainValidationError(
            f"{matrix.valid_count} valid runs exceed max_runs {config.max_runs}"
        )


def _scenarios_for(config: ExperimentConfig) -> tuple[str, ...]:
    if config.block == "e3" and config.split == "development":
        return tuple(spec.id for spec in list_scenarios())
    if config.block == "e3":
        raise DomainValidationError("block e3 uses the development split")
    return config.scenarios


def _load(split: str, scenario_id: str) -> ScenarioSpec:
    if split == "evaluation":
        return load_heldout(scenario_id)[0]
    try:
        return load_scenario(scenario_id)[0]
    except DomainValidationError:
        raise DomainValidationError(f"development split cannot load {scenario_id}") from None


def _exclude(
    deletion_source: str | None, policy: DeletionPolicy, split: str, scenario_id: str
) -> str | None:
    if split == "development" and scenario_id.startswith("heldout-"):
        return "held-out template is not in the development split"
    if policy is not DeletionPolicy.NO_DELETION and deletion_source is None:
        return f"{policy.value} does not apply to a scenario without a deletion source"
    return None
