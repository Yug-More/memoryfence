"""Deterministic workspace fixtures for Phase 2 tests."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from memoryfence.domain.enums import LineageFidelity, SourceVisibility, WorkspaceRole
from memoryfence.domain.ids import UserId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef, User, Workspace
from memoryfence.domain.provenance import ProvenanceDegradationConfiguration
from memoryfence.domain.sources import SourceDocument, SourceRevision
from memoryfence.domain.time import StepClock
from memoryfence.groundtruth import open_episode
from memoryfence.observability import Auditor
from memoryfence.storage.database import EpisodeDatabase
from memoryfence.workspace.deletion import DeletionService
from memoryfence.workspace.directory import DirectoryService
from memoryfence.workspace.memories import MemoryService
from memoryfence.workspace.sources import SourceService
from memoryfence.workspace.tools import ToolService

DEGRADATION = ProvenanceDegradationConfiguration(
    fidelity=LineageFidelity.LF1_0,
    master_seed=7,
    scenario_template="sf1",
    payload_variant="explicit",
    replicate=0,
)


@dataclass
class Lab:
    database: EpisodeDatabase
    auditor: Auditor
    directory: DirectoryService
    sources: SourceService
    memories: MemoryService
    deletion: DeletionService
    tools: ToolService
    admin: User
    workspace: Workspace

    def actor(self, user: User) -> PrincipalRef:
        return PrincipalRef.user(user.id)

    def add_user(self, name: str, role: WorkspaceRole) -> User:
        user = self.directory.register_user(name)
        self.directory.grant_membership(self.actor(self.admin), self.workspace.id, user.id, role)
        return user

    def add_source(
        self,
        owner: User,
        *,
        title: str = "Notes",
        content: str = "benign note",
        visibility: SourceVisibility = SourceVisibility.WORKSPACE,
    ) -> tuple[SourceDocument, SourceRevision]:
        return self.sources.create(
            self.actor(owner),
            self.workspace.id,
            title=title,
            content=content,
            visibility=visibility,
        )


@pytest.fixture
def lab(tmp_path: Path) -> Iterator[Lab]:
    clock = StepClock(datetime(2026, 1, 1, tzinfo=UTC), timedelta(seconds=1))
    database = open_episode(tmp_path, clock)
    auditor = Auditor(database)
    directory = DirectoryService(database, auditor)
    admin = directory.register_user("Admin")
    workspace, _membership = directory.create_workspace(admin.id, "Team")
    built = Lab(
        database=database,
        auditor=auditor,
        directory=directory,
        sources=SourceService(auditor),
        memories=MemoryService(auditor, DEGRADATION),
        deletion=DeletionService(auditor),
        tools=ToolService(auditor),
        admin=admin,
        workspace=workspace,
    )
    try:
        yield built
    finally:
        database.dispose()


@pytest.fixture
def workspace_id(lab: Lab) -> WorkspaceId:
    return lab.workspace.id


@pytest.fixture
def admin_id(lab: Lab) -> UserId:
    return lab.admin.id
