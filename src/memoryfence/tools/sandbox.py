"""Synthetic tickets and notes.

An unknown tool name is denied here even when the caller has ``tool.execute``.
The denial does not read a model justification; this method does not accept one.
"""

from memoryfence.domain.access import AuthorizationDecision, ResourceRef
from memoryfence.domain.base import DomainModel
from memoryfence.domain.enums import EventCategory, Operation, Permission, ResourceKind
from memoryfence.domain.errors import (
    AuthorizationDenied,
    DomainValidationError,
    ReasonCode,
    ResourceNotFound,
)
from memoryfence.domain.ids import IdPrefix, NoteId, ProposalId, SandboxId, TicketId, WorkspaceId
from memoryfence.domain.principals import PrincipalRef
from memoryfence.domain.serialization import canonical_json
from memoryfence.domain.tools import ToolName
from memoryfence.observability import Auditor
from memoryfence.storage.database import UnitOfWork
from memoryfence.storage.schema import SandboxEffectRow, SandboxNoteRow, SandboxTicketRow
from memoryfence.workspace.authority import Authorizer

ALLOWED_TOOLS = frozenset({"create_ticket", "update_task", "add_note"})
_TICKET_STATUS = frozenset({"open", "closed"})


class SandboxEffect(DomainModel):
    id: SandboxId
    tool_name: ToolName
    ticket_id: TicketId | None
    note_id: NoteId | None


class Sandbox:
    def __init__(self, auditor: Auditor) -> None:
        self._auditor = auditor

    def execute(
        self,
        actor: PrincipalRef | None,
        workspace_id: WorkspaceId,
        proposal_id: ProposalId,
        tool_name: str,
        arguments: tuple[tuple[str, str], ...],
    ) -> SandboxEffect:
        resource = ResourceRef(kind=ResourceKind.TOOL_PROPOSAL, id=proposal_id)
        with self._auditor.operation(
            EventCategory.SANDBOX,
            Operation.SANDBOX_EXECUTE,
            actor=actor,
            workspace_id=workspace_id,
            resource=resource,
        ) as scope:
            authorizer = Authorizer(scope.uow.session)
            facts = authorizer.require(actor, Permission.TOOL_EXECUTE, workspace_id)
            if tool_name not in ALLOWED_TOOLS:
                raise AuthorizationDenied(
                    AuthorizationDecision(
                        allowed=False,
                        reason=ReasonCode.UNKNOWN_TOOL,
                        permission=Permission.TOOL_EXECUTE,
                        principal=facts.principal,
                        workspace_id=workspace_id,
                        resource=resource,
                    )
                )
            args = _arguments(arguments)
            ticket_id: str | None = None
            note_id: str | None = None
            if tool_name == "create_ticket":
                ticket_id = _create_ticket(scope.uow, workspace_id, args)
            elif tool_name == "update_task":
                ticket_id = _update_ticket(scope.uow, workspace_id, args)
            else:
                note_id = _add_note(scope.uow, workspace_id, args)
            effect_id = scope.uow.next_id(IdPrefix.SANDBOX)
            scope.uow.session.add(
                SandboxEffectRow(
                    id=effect_id,
                    workspace_id=workspace_id,
                    proposal_id=proposal_id,
                    tool_name=tool_name,
                    arguments_json=canonical_json([list(pair) for pair in arguments]),
                    ticket_id=ticket_id,
                    note_id=note_id,
                    created_at=scope.uow.now(),
                )
            )
            scope.uow.session.flush()
            scope.details["tool_name"] = tool_name
            scope.details["proposal_id"] = proposal_id
            effect = SandboxEffect(
                id=SandboxId(effect_id),
                tool_name=tool_name,
                ticket_id=TicketId(ticket_id) if ticket_id is not None else None,
                note_id=NoteId(note_id) if note_id is not None else None,
            )
        return effect


def _arguments(arguments: tuple[tuple[str, str], ...]) -> dict[str, str]:
    names = [name for name, _value in arguments]
    if len(names) != len(set(names)):
        raise DomainValidationError("tool argument names must be unique")
    return dict(arguments)


def _require(args: dict[str, str], name: str) -> str:
    value = args.get(name, "")
    if not value:
        raise DomainValidationError(f"sandbox tool requires {name}")
    return value


def _create_ticket(uow: UnitOfWork, workspace_id: WorkspaceId, args: dict[str, str]) -> str:
    ticket_id = uow.next_id(IdPrefix.TICKET)
    now = uow.now()
    uow.session.add(
        SandboxTicketRow(
            id=ticket_id,
            workspace_id=workspace_id,
            title=_require(args, "title"),
            body=_require(args, "body"),
            status="open",
            created_at=now,
            updated_at=now,
        )
    )
    uow.session.flush()
    return ticket_id


def _update_ticket(uow: UnitOfWork, workspace_id: WorkspaceId, args: dict[str, str]) -> str:
    ticket_id = _require(args, "ticket_id")
    status = _require(args, "status")
    if status not in _TICKET_STATUS:
        raise DomainValidationError("ticket status must be open or closed")
    row = uow.session.get(SandboxTicketRow, ticket_id)
    if row is None or row.workspace_id != workspace_id:
        raise ResourceNotFound("sandbox ticket", ticket_id)
    row.status = status
    row.updated_at = uow.now()
    uow.session.flush()
    return ticket_id


def _add_note(uow: UnitOfWork, workspace_id: WorkspaceId, args: dict[str, str]) -> str:
    note_id = uow.next_id(IdPrefix.NOTE)
    uow.session.add(
        SandboxNoteRow(
            id=note_id,
            workspace_id=workspace_id,
            body=_require(args, "text"),
            created_at=uow.now(),
        )
    )
    uow.session.flush()
    return note_id
