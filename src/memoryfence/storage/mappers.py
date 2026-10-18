"""Conversions from ORM rows to validated domain models.

Every conversion re-validates, so a row that violates a domain invariant surfaces as an
error instead of an invalid object.
"""

import json

from memoryfence.domain.deletion import RederivationTask
from memoryfence.domain.enums import Permission, PrincipalKind
from memoryfence.domain.ids import (
    AgentId,
    DeletionId,
    MemoryId,
    RevisionId,
    SourceId,
    TaskId,
    TransformationId,
    UserId,
    WorkspaceId,
)
from memoryfence.domain.memories import Memory, TransformationRecord
from memoryfence.domain.principals import (
    Agent,
    InstructionAuthority,
    PrincipalRef,
    User,
    Workspace,
    WorkspaceMembership,
)
from memoryfence.domain.provenance import RecordedProvenanceNode
from memoryfence.domain.sources import SourceAccessGrant, SourceDocument, SourceRevision
from memoryfence.storage.schema import (
    AgentRow,
    InstructionAuthorityRow,
    MembershipRow,
    MemoryRow,
    RecordedNodeRow,
    RederivationTaskRow,
    SourceAccessGrantRow,
    SourceRevisionRow,
    SourceRow,
    TransformationRow,
    UserRow,
    WorkspaceRow,
)


def principal_ref(kind: PrincipalKind, identifier: str) -> PrincipalRef:
    return PrincipalRef(kind=kind, id=identifier)


def to_user(row: UserRow) -> User:
    return User(id=UserId(row.id), display_name=row.display_name, created_at=row.created_at)


def to_workspace(row: WorkspaceRow) -> Workspace:
    return Workspace(id=WorkspaceId(row.id), name=row.name, created_at=row.created_at)


def to_membership(row: MembershipRow) -> WorkspaceMembership:
    return WorkspaceMembership(
        workspace_id=WorkspaceId(row.workspace_id),
        user_id=UserId(row.user_id),
        role=row.role,
        state=row.state,
        granted_at=row.granted_at,
        revoked_at=row.revoked_at,
    )


def to_agent(row: AgentRow, permissions: frozenset[Permission]) -> Agent:
    return Agent(
        id=AgentId(row.id),
        workspace_id=WorkspaceId(row.workspace_id),
        controlling_user_id=UserId(row.controlling_user_id),
        display_name=row.display_name,
        delegated_permissions=permissions,
        state=row.state,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
    )


def to_instruction_authority(row: InstructionAuthorityRow) -> InstructionAuthority:
    return InstructionAuthority(
        workspace_id=WorkspaceId(row.workspace_id),
        authority_user_id=UserId(row.authority_user_id),
        subject_user_id=UserId(row.subject_user_id),
        granted_at=row.granted_at,
    )


def to_source(row: SourceRow) -> SourceDocument:
    return SourceDocument(
        id=SourceId(row.id),
        workspace_id=WorkspaceId(row.workspace_id),
        owner_user_id=UserId(row.owner_user_id),
        title=row.title,
        visibility=row.visibility,
        deletion_state=row.deletion_state,
        deletion_policy=row.deletion_policy,
        created_at=row.created_at,
        deleted_at=row.deleted_at,
    )


def to_revision(row: SourceRevisionRow) -> SourceRevision:
    return SourceRevision(
        id=RevisionId(row.id),
        source_id=SourceId(row.source_id),
        sequence=row.sequence,
        author_user_id=UserId(row.author_user_id),
        content=row.content,
        content_sha256=row.content_sha256,
        created_at=row.created_at,
    )


def to_grant(row: SourceAccessGrantRow) -> SourceAccessGrant:
    return SourceAccessGrant(
        source_id=SourceId(row.source_id),
        user_id=UserId(row.user_id),
        granted_at=row.granted_at,
        revoked_at=row.revoked_at,
    )


def to_transformation(row: TransformationRow) -> TransformationRecord:
    return TransformationRecord(
        id=TransformationId(row.id),
        workspace_id=WorkspaceId(row.workspace_id),
        transformation_type=row.transformation_type,
        prompt_version=row.prompt_version,
        derivation_round=row.derivation_round,
        performed_by=principal_ref(row.performed_by_kind, row.performed_by_id),
        created_at=row.created_at,
    )


def to_memory(row: MemoryRow) -> Memory:
    return Memory(
        id=MemoryId(row.id),
        workspace_id=WorkspaceId(row.workspace_id),
        memory_type=row.memory_type,
        state=row.state,
        visibility=row.visibility,
        owner_user_id=UserId(row.owner_user_id) if row.owner_user_id is not None else None,
        content=row.content,
        content_sha256=row.content_sha256,
        source_revision_id=(
            RevisionId(row.source_revision_id) if row.source_revision_id is not None else None
        ),
        transformation_id=(
            TransformationId(row.transformation_id) if row.transformation_id is not None else None
        ),
        derivation_round=row.derivation_round,
        created_at=row.created_at,
        revoked_at=row.revoked_at,
    )


def to_recorded_node(row: RecordedNodeRow) -> RecordedProvenanceNode:
    return RecordedProvenanceNode(
        memory_id=MemoryId(row.memory_id),
        workspace_id=WorkspaceId(row.workspace_id),
        memory_type=row.memory_type,
        source_id=SourceId(row.source_id) if row.source_id is not None else None,
        author_user_id=UserId(row.author_user_id) if row.author_user_id is not None else None,
        marked_incomplete=row.marked_incomplete,
        created_at=row.created_at,
    )


def to_rederivation_task(row: RederivationTaskRow) -> RederivationTask:
    return RederivationTask(
        id=TaskId(row.id),
        deletion_id=DeletionId(row.deletion_id),
        workspace_id=WorkspaceId(row.workspace_id),
        replaces_memory_id=MemoryId(row.replaces_memory_id),
        transformation_id=TransformationId(row.transformation_id),
        surviving_input_ids=tuple(MemoryId(item) for item in json.loads(row.surviving_input_ids)),
        depends_on_task_ids=tuple(TaskId(item) for item in json.loads(row.depends_on_task_ids)),
        status=row.status,
        created_at=row.created_at,
    )
