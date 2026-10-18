"""Error hierarchy and stable reason codes.

Messages name only the operation and public identifiers. They never include memory
content, provenance, or ground-truth labels.
"""

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from memoryfence.domain.access import AuthorizationDecision


class ReasonCode(StrEnum):
    OK = "ok"
    ALLOWED = "allowed"

    MISSING_PRINCIPAL = "denied.missing_principal"
    UNKNOWN_PRINCIPAL = "denied.unknown_principal"
    NOT_A_MEMBER = "denied.not_a_member"
    MEMBERSHIP_REVOKED = "denied.membership_revoked"
    CROSS_WORKSPACE = "denied.cross_workspace"
    PERMISSION_NOT_GRANTED = "denied.permission_not_granted"
    AGENT_INACTIVE = "denied.agent_inactive"
    AGENT_NOT_DELEGATED = "denied.agent_not_delegated"
    AGENT_CANNOT_DELEGATE = "denied.agent_cannot_delegate"
    DELEGATION_EXCEEDS_PRINCIPAL = "denied.delegation_exceeds_principal"
    NOT_CONTROLLING_PRINCIPAL = "denied.not_controlling_principal"
    NOT_OWNER = "denied.not_owner"
    SOURCE_NOT_VISIBLE = "denied.source_not_visible"
    SOURCE_UNAVAILABLE = "denied.source_unavailable"
    MEMORY_NOT_VISIBLE = "denied.memory_not_visible"
    MEMORY_REVOKED = "denied.memory_revoked"
    UNSUPPORTED_REQUEST = "denied.unsupported_request"

    NOT_FOUND = "error.not_found"
    DUPLICATE_IDENTIFIER = "error.duplicate_identifier"
    CONFLICT = "error.conflict"
    INVALID_TRANSITION = "error.invalid_transition"
    VALIDATION_FAILED = "error.validation_failed"
    LINEAGE_INVALID_PARENT = "error.lineage_invalid_parent"
    LINEAGE_CROSS_WORKSPACE = "error.lineage_cross_workspace"
    LINEAGE_CYCLE = "error.lineage_cycle"
    LINEAGE_MALFORMED = "error.lineage_malformed"
    PERSISTENCE_FAILURE = "error.persistence_failure"
    SCHEMA_VERSION_MISMATCH = "error.schema_version_mismatch"
    SCRIPT_MISS = "error.script_miss"
    SCRIPT_TIMEOUT = "error.script_timeout"
    MODEL_UNAVAILABLE = "error.model_unavailable"
    MODEL_TIMEOUT = "error.model_timeout"
    MODEL_OUTPUT = "error.model_output"
    STEP_LIMIT = "error.step_limit"
    UNKNOWN_TOOL = "denied.unknown_tool"
    DEFENSE_POLICY = "denied.defense_policy"
    DEFENSE_LINEAGE = "denied.defense_lineage"
    DEFENSE_FAILED = "error.defense_failed"

    @property
    def is_denial(self) -> bool:
        return self.value.startswith("denied.")


class MemoryFenceError(Exception):
    """Base class. Every subclass carries a stable reason code."""

    def __init__(self, code: ReasonCode, message: str) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code


class DomainValidationError(MemoryFenceError):
    def __init__(self, message: str) -> None:
        super().__init__(ReasonCode.VALIDATION_FAILED, message)


class AuthorizationDenied(MemoryFenceError):  # noqa: N818 - a denial is not an "error"
    def __init__(self, decision: "AuthorizationDecision") -> None:
        super().__init__(decision.reason, f"{decision.permission.value} denied")
        self.decision = decision


class ResourceNotFound(MemoryFenceError):  # noqa: N818
    def __init__(self, kind: str, identifier: str) -> None:
        super().__init__(ReasonCode.NOT_FOUND, f"{kind} {identifier} not found")


class ConflictError(MemoryFenceError):
    def __init__(self, message: str, code: ReasonCode = ReasonCode.CONFLICT) -> None:
        super().__init__(code, message)


class InvalidTransitionError(MemoryFenceError):
    def __init__(self, message: str) -> None:
        super().__init__(ReasonCode.INVALID_TRANSITION, message)


class ProvenanceIntegrityError(MemoryFenceError):
    pass


class PersistenceError(MemoryFenceError):
    def __init__(self, message: str, code: ReasonCode = ReasonCode.PERSISTENCE_FAILURE) -> None:
        super().__init__(code, message)


class ModelBackendError(MemoryFenceError):
    """A local model call failed. The message does not include model output or memory text."""

    def __init__(self, code: ReasonCode, message: str) -> None:
        super().__init__(code, message)


class ModelScriptError(MemoryFenceError):
    """The scripted backend has no fixture for this call, or the fixture simulates a failure."""

    def __init__(self, message: str, *, timeout: bool = False) -> None:
        code = ReasonCode.SCRIPT_TIMEOUT if timeout else ReasonCode.SCRIPT_MISS
        super().__init__(code, message)
