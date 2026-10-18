from types import MappingProxyType

from memoryfence.domain.enums import Permission, WorkspaceRole

_VIEWER = frozenset(
    {
        Permission.SOURCE_READ,
        Permission.MEMORY_READ,
        Permission.AGENT_REGISTER,
    }
)
_MEMBER = _VIEWER | {
    Permission.SOURCE_CREATE,
    Permission.SOURCE_REVISE,
    Permission.SOURCE_MANAGE_ACCESS,
    Permission.SOURCE_DELETE,
    Permission.MEMORY_CREATE,
    Permission.MEMORY_TRANSFORM,
    Permission.TOOL_PROPOSE,
    Permission.TOOL_EXECUTE,
}
_MODERATOR = _MEMBER | {Permission.SOURCE_MODERATE}
_ADMIN = _MODERATOR | {Permission.MEMBERSHIP_MANAGE, Permission.AGENT_MANAGE}

ROLE_PERMISSIONS = MappingProxyType(
    {
        WorkspaceRole.VIEWER: _VIEWER,
        WorkspaceRole.MEMBER: _MEMBER,
        WorkspaceRole.MODERATOR: _MODERATOR,
        WorkspaceRole.ADMIN: _ADMIN,
    }
)
