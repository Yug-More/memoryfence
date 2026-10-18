"""Enumerations. Values are stable strings because they are persisted and logged."""

from enum import StrEnum


class PrincipalKind(StrEnum):
    """``user``: an authenticated human. ``agent``: an AI agent acting for one user."""

    USER = "user"
    AGENT = "agent"


class WorkspaceRole(StrEnum):
    """Roles in increasing order of authority. Permissions are listed in ``access``."""

    VIEWER = "viewer"
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Permission(StrEnum):
    """Capabilities a role grants and an agent may be delegated.

    ``source.delete`` covers sources the acting user owns; ``source.moderate`` covers
    deleting other principals' sources. ``source.manage_access`` covers grants on owned
    restricted sources. ``agent.register`` lets a user register their own agents;
    ``agent.manage`` lets an admin revoke anyone's agents.
    """

    SOURCE_READ = "source.read"
    SOURCE_CREATE = "source.create"
    SOURCE_REVISE = "source.revise"
    SOURCE_MANAGE_ACCESS = "source.manage_access"
    SOURCE_DELETE = "source.delete"
    SOURCE_MODERATE = "source.moderate"
    MEMORY_READ = "memory.read"
    MEMORY_CREATE = "memory.create"
    MEMORY_TRANSFORM = "memory.transform"
    MEMBERSHIP_MANAGE = "membership.manage"
    AGENT_REGISTER = "agent.register"
    AGENT_MANAGE = "agent.manage"
    TOOL_PROPOSE = "tool.propose"
    TOOL_EXECUTE = "tool.execute"


class MembershipState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class AgentState(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class SourceVisibility(StrEnum):
    """``workspace``: every active member. ``restricted``: owner plus explicit grants.
    ``private``: owner only."""

    WORKSPACE = "workspace"
    RESTRICTED = "restricted"
    PRIVATE = "private"


class SourceDeletionState(StrEnum):
    """``tombstoned``: unreadable, record and revisions retained (``DS2``).
    ``deleted``: revisions and title removed; a content-free stub remains for audit."""

    ACTIVE = "active"
    TOMBSTONED = "tombstoned"
    DELETED = "deleted"


class MemoryType(StrEnum):
    """``primary``: extracted from one source revision. ``derived``: produced by a
    transformation over one or more memories."""

    PRIMARY = "primary"
    DERIVED = "derived"


class MemoryState(StrEnum):
    """``revoked``: retained in the store but excluded from reads and retrieval."""

    ACTIVE = "active"
    REVOKED = "revoked"


class MemoryVisibility(StrEnum):
    """``inherit_source``: primary memories follow their source's ACL at read time.
    ``workspace`` and ``private`` are materialized for derived memories at creation."""

    INHERIT_SOURCE = "inherit_source"
    WORKSPACE = "workspace"
    PRIVATE = "private"


class TransformationType(StrEnum):
    """Protocol section 3.1. ``TT0`` (no transformation) is the absence of a record."""

    EXTRACTIVE_SUMMARY = "TT1"
    ABSTRACTIVE_SUMMARY = "TT2"
    CONSOLIDATION = "TT3"
    REFLECTION = "TT4"


class LineageFidelity(StrEnum):
    """Protocol section 3.3: the probability that each true derivation edge is recorded."""

    LF1_0 = "LF1.0"
    LF0_75 = "LF0.75"
    LF0_5 = "LF0.5"
    LF0_0 = "LF0.0"

    @property
    def retention_probability(self) -> float:
        return float(self.value.removeprefix("LF"))

    @property
    def completeness(self) -> "ProvenanceCompleteness":
        if self is LineageFidelity.LF1_0:
            return ProvenanceCompleteness.COMPLETE
        if self is LineageFidelity.LF0_0:
            return ProvenanceCompleteness.ABSENT
        return ProvenanceCompleteness.PARTIALLY_MISSING


class ProvenanceCompleteness(StrEnum):
    """The three provenance conditions named in the research question."""

    COMPLETE = "complete"
    PARTIALLY_MISSING = "partially_missing"
    ABSENT = "absent"


class MissingnessMode(StrEnum):
    """``silent`` is the primary design. ``marked`` is exploratory only (analysis X10)."""

    SILENT = "silent"
    MARKED = "marked"


class DeletionPolicy(StrEnum):
    """Protocol section 3.2."""

    NO_DELETION = "DS0"
    SOURCE_AND_PRIMARY = "DS1"
    TOMBSTONE_AND_REVOKE = "DS2"
    CASCADE = "DS3"
    CASCADE_AND_REDERIVE = "DS4"


class DeletionScenario(StrEnum):
    """Threat model section 4.5: who triggers the deletion."""

    ATTACKER = "D-attacker"
    MODERATOR = "D-moderator"
    RETENTION = "D-retention"


class DeletionEffect(StrEnum):
    """One row of the harness-only deletion ledger."""

    SOURCE_TOMBSTONED = "source_tombstoned"
    SOURCE_DELETED = "source_deleted"
    REVISION_DELETED = "revision_deleted"
    MEMORY_REVOKED = "memory_revoked"
    MEMORY_DELETED = "memory_deleted"
    REDERIVATION_PENDING = "rederivation_pending"
    NOT_REGENERATED = "not_regenerated"


class RederivationStatus(StrEnum):
    """``pending``: awaiting execution. ``completed``: a replacement memory was written.
    ``not_regenerated``: no recorded input survives, so the protocol does not regenerate."""

    PENDING = "pending"
    COMPLETED = "completed"
    NOT_REGENERATED = "not_regenerated"


class ModelPurpose(StrEnum):
    """Why a model backend was called. The scripted backend matches this exactly."""

    TRANSFORM = "transform"
    AGENT = "agent"


class SourceOrigin(StrEnum):
    """Ground-truth label of a source's author role. Evaluator-only."""

    ATTACKER = "attacker"
    BENIGN = "benign"


class ResourceKind(StrEnum):
    WORKSPACE = "workspace"
    USER = "user"
    AGENT = "agent"
    MEMBERSHIP = "membership"
    SOURCE = "source"
    REVISION = "revision"
    MEMORY = "memory"
    TOOL_PROPOSAL = "tool_proposal"
    RUN = "run"


class ToolStage(StrEnum):
    PROPOSE = "propose"
    EXECUTE = "execute"


class EventCategory(StrEnum):
    DIRECTORY = "directory"
    SOURCE = "source"
    MEMORY = "memory"
    DELETION = "deletion"
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    MODEL = "model"
    AGENT = "agent"
    SANDBOX = "sandbox"


class Operation(StrEnum):
    USER_REGISTER = "user.register"
    WORKSPACE_CREATE = "workspace.create"
    MEMBERSHIP_GRANT = "membership.grant"
    MEMBERSHIP_REVOKE = "membership.revoke"
    AGENT_REGISTER = "agent.register"
    AGENT_REVOKE = "agent.revoke"
    INSTRUCTION_AUTHORITY_GRANT = "instruction_authority.grant"
    SOURCE_CREATE = "source.create"
    SOURCE_REVISE = "source.revise"
    SOURCE_READ = "source.read"
    SOURCE_GRANT_ACCESS = "source.grant_access"
    SOURCE_REVOKE_ACCESS = "source.revoke_access"
    SOURCE_DELETE = "source.delete"
    MEMORY_EXTRACT = "memory.extract"
    MEMORY_DERIVE = "memory.derive"
    MEMORY_READ = "memory.read"
    TOOL_AUTHORIZE = "tool.authorize"
    SOURCE_INGEST = "source.ingest"
    MEMORY_RETRIEVE = "memory.retrieve"
    MEMORY_REDERIVE = "memory.rederive"
    MODEL_COMPLETE = "model.complete"
    SANDBOX_EXECUTE = "sandbox.execute"
    AGENT_STEP = "agent.step"


class EventOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    DENIED = "denied"
    FAILED = "failed"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

    @property
    def is_terminal(self) -> bool:
        return self is not RunStatus.RUNNING
