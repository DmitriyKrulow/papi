from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class Permission(str, Enum):
    CREATE_ASSET = "create_asset"
    UPDATE_ASSET = "update_asset"
    DELETE_ASSET = "delete_asset"
    VIEW_ASSET = "view_asset"
    APPROVE_REPAIR = "approve_repair"
    MANAGE_USERS = "manage_users"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"


ROLE_PERMISSIONS = {
    UserRole.ADMIN: set(Permission),
    UserRole.MANAGER: {
        Permission.CREATE_ASSET,
        Permission.UPDATE_ASSET,
        Permission.DELETE_ASSET,
        Permission.VIEW_ASSET,
        Permission.APPROVE_REPAIR,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_DATA,
    },
    UserRole.USER: {
        Permission.CREATE_ASSET,
        Permission.UPDATE_ASSET,
        Permission.VIEW_ASSET,
        Permission.VIEW_REPORTS,
    },
    UserRole.VIEWER: {
        Permission.VIEW_ASSET,
        Permission.VIEW_REPORTS,
    },
}


def has_permission(user_role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user_role, set())


def has_any_permission(user_role: UserRole, permissions: list[Permission]) -> bool:
    user_permissions = ROLE_PERMISSIONS.get(user_role, set())
    return any(permission in user_permissions for permission in permissions)
