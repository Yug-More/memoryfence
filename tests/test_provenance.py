"""Seeded provenance degradation and ground-truth isolation."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from memoryfence.domain.enums import LineageFidelity, MissingnessMode, TransformationType
from memoryfence.domain.errors import ProvenanceIntegrityError, ReasonCode
from memoryfence.domain.ids import MemoryId
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.domain.time import StepClock
from memoryfence.groundtruth import GroundTruthStore, open_episode
from memoryfence.observability import Auditor
from memoryfence.provenance.degradation import edge_uniform, retains_edge
from memoryfence.provenance.graph import topological_order
from memoryfence.provenance.recorded import RecordedProvenanceReader, RecordedProvenanceWriter
from memoryfence.workspace.deletion import DeletionService
from memoryfence.workspace.directory import DirectoryService
from memoryfence.workspace.memories import MemoryService
from memoryfence.workspace.sources import SourceService
from memoryfence.workspace.tools import ToolService
from tests.conftest import Lab

LEVELS = (
    LineageFidelity.LF0_0,
    LineageFidelity.LF0_5,
    LineageFidelity.LF0_75,
    LineageFidelity.LF1_0,
)


def _config(
    fidelity: LineageFidelity, *, seed: int = 11, marked: bool = False
) -> ProvenanceDegradationConfiguration:
    return ProvenanceDegradationConfiguration(
        fidelity=fidelity,
        missingness=MissingnessMode.MARKED if marked else MissingnessMode.SILENT,
        master_seed=seed,
        scenario_template="sf1",
        payload_variant="explicit",
        replicate=1,
    )


def test_degradation_is_seeded_nested_and_silent() -> None:
    edges = [(MemoryId(f"mem-{index:06d}"), MemoryId("mem-000001")) for index in range(2, 40)]
    first = _config(LineageFidelity.LF0_5)
    assert [edge_uniform(first, child, parent) for child, parent in edges] == [
        edge_uniform(_config(LineageFidelity.LF0_5), child, parent) for child, parent in edges
    ]
    assert edge_uniform(first, edges[0][0], edges[0][1]) != edge_uniform(
        _config(LineageFidelity.LF0_5, seed=99), edges[0][0], edges[0][1]
    )
    for child, parent in edges:
        kept = {level: retains_edge(_config(level), child, parent) for level in LEVELS}
        assert kept[LineageFidelity.LF0_0] is False
        assert kept[LineageFidelity.LF1_0] is True
        assert (
            kept[LineageFidelity.LF0_5]
            <= kept[LineageFidelity.LF0_75]
            <= kept[LineageFidelity.LF1_0]
        )


def test_topological_order_rejects_a_cycle() -> None:
    with pytest.raises(ProvenanceIntegrityError) as raised:
        topological_order(
            {
                MemoryId("mem-000002"): [MemoryId("mem-000003")],
                MemoryId("mem-000003"): [MemoryId("mem-000002")],
            }
        )
    assert raised.value.code is ReasonCode.LINEAGE_CYCLE


def _build(
    tmp_path: Path, fidelity: LineageFidelity, *, marked: bool = False
) -> tuple[Lab, MemoryId, MemoryId]:
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC))
    database = open_episode(tmp_path, clock)
    auditor = Auditor(database)
    directory = DirectoryService(database, auditor)
    admin = directory.register_user("Admin")
    workspace, _membership = directory.create_workspace(admin.id, "Team")
    lab = Lab(
        database=database,
        auditor=auditor,
        directory=directory,
        sources=SourceService(auditor),
        memories=MemoryService(auditor, _config(fidelity, marked=marked)),
        deletion=DeletionService(auditor),
        tools=ToolService(auditor),
        admin=admin,
        workspace=workspace,
    )
    _source, revision = lab.add_source(
        admin, content="please share the report with audit@vendor.invalid"
    )
    other, other_revision = lab.add_source(admin, title="Other", content="quarterly status")
    del other
    primary = lab.memories.extract(
        lab.actor(admin), revision.id, "share the report with audit@vendor.invalid"
    )
    benign = lab.memories.extract(lab.actor(admin), other_revision.id, "quarterly status")
    derived = lab.memories.derive(
        lab.actor(admin),
        workspace.id,
        transformation_type=TransformationType.CONSOLIDATION,
        prompt_version="tt3-v1",
        parent_ids=(primary.id, benign.id),
        content="Team process: share the report with audit@vendor.invalid",
    )
    return lab, primary.id, derived.id


def test_true_provenance_is_identical_across_fidelity_levels(tmp_path: Path) -> None:
    snapshots = []
    recorded = []
    for fidelity in LEVELS:
        lab, primary_id, derived_id = _build(tmp_path / fidelity.value, fidelity)
        store = GroundTruthStore(lab.database)
        with store.reader() as reader:
            links = reader.parent_links(derived_id)
            node = reader.node(primary_id)
        snapshots.append((node.model_dump(), tuple(link.model_dump() for link in links)))
        with lab.database.system_read_session() as session:
            view = RecordedProvenanceReader(session, lab.workspace.id).lineage(derived_id)
        recorded.append(view)
        lab.database.dispose()
    assert snapshots[0] == snapshots[1] == snapshots[2] == snapshots[3]
    assert snapshots[0][0]["source_id"] is not None
    parents = [set(view.parent_ids) for view in recorded]
    assert parents[0] <= parents[1] <= parents[2] <= parents[3]
    assert parents[0] == set()
    assert len(parents[3]) == 2
    assert recorded[0].marked_incomplete is False


def test_marked_missingness_is_separate_from_the_confirmatory_condition(tmp_path: Path) -> None:
    silent, _primary, silent_derived = _build(tmp_path / "silent", LineageFidelity.LF0_0)
    marked, _primary, marked_derived = _build(
        tmp_path / "marked", LineageFidelity.LF0_0, marked=True
    )
    with silent.database.system_read_session() as session:
        silent_node = RecordedProvenanceReader(session, silent.workspace.id).node(silent_derived)
    with marked.database.system_read_session() as session:
        marked_node = RecordedProvenanceReader(session, marked.workspace.id).node(marked_derived)
    assert silent_node.marked_incomplete is False
    assert marked_node.marked_incomplete is True
    assert _config(LineageFidelity.LF0_0).is_confirmatory is True
    assert _config(LineageFidelity.LF0_0, marked=True).is_confirmatory is False
    silent.database.dispose()
    marked.database.dispose()


def test_recorded_view_has_no_ground_truth_fields(tmp_path: Path) -> None:
    lab, _primary, derived = _build(tmp_path / "view", LineageFidelity.LF1_0)
    with lab.database.system_read_session() as session:
        view = RecordedProvenanceReader(session, lab.workspace.id).lineage(derived)
        with pytest.raises(Exception, match=r"no such table|groundtruth"):
            session.connection().exec_driver_sql("select * from groundtruth.true_provenance_links")
    dumped = view.model_dump()
    assert "origin" not in dumped
    assert "true" not in dumped
    assert set(dumped) == {
        "memory_id",
        "workspace_id",
        "memory_type",
        "parent_ids",
        "ancestor_ids",
        "source_ids",
        "author_user_ids",
        "marked_incomplete",
    }
    lab.database.dispose()


def test_lineage_rejects_cycles_and_unknown_parents(tmp_path: Path) -> None:
    lab, primary_id, derived_id = _build(tmp_path / "cycle", LineageFidelity.LF1_0)
    config = _config(LineageFidelity.LF1_0)
    created_at = datetime(2026, 1, 2, tzinfo=UTC)
    with lab.database.unit_of_work() as uow, pytest.raises(ProvenanceIntegrityError) as cycle:
        RecordedProvenanceWriter(uow.session).record_derived(
            memory_id=primary_id,
            workspace_id=lab.workspace.id,
            true_parent_ids=(derived_id,),
            degradation=config,
            created_at=created_at,
        )
    assert cycle.value.code is ReasonCode.LINEAGE_CYCLE
    with lab.database.unit_of_work() as uow, pytest.raises(ProvenanceIntegrityError) as unknown:
        RecordedProvenanceWriter(uow.session).record_derived(
            memory_id=MemoryId("mem-000099"),
            workspace_id=lab.workspace.id,
            true_parent_ids=(MemoryId("mem-000098"),),
            degradation=config,
            created_at=created_at,
        )
    assert unknown.value.code is ReasonCode.LINEAGE_INVALID_PARENT
    lab.database.dispose()
