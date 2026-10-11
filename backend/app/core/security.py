from fastapi import Header, HTTPException, status, Depends
from typing import Optional
from app.models.audit import UserRole
from app.config import settings
import logging

logger = logging.getLogger("cloudsentinel.security")


class CurrentUser:
    def __init__(self, uid: str, email: str, role: UserRole):
        self.uid = uid
        self.email = email
        self.role = role


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_demo_role: Optional[str] = Header("ADMIN")
) -> CurrentUser:
    """
    Authenticates requests using Firebase ID tokens when configured,
    or falls back cleanly to Demo Role mode (ADMIN, OPERATOR, VIEWER).
    """
    # 1. If Firebase credentials and token present, attempt verification
    if settings.FIREBASE_PROJECT_ID and authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
        try:
            import firebase_admin
            from firebase_admin import auth
            decoded_token = auth.verify_id_token(token)
            role_str = decoded_token.get("role", "OPERATOR").upper()
            role = UserRole(role_str) if role_str in UserRole._value2member_map_ else UserRole.OPERATOR
            return CurrentUser(
                uid=decoded_token.get("uid", "firebase-user"),
                email=decoded_token.get("email", "operator@cloudsentinel.io"),
                role=role
            )
        except Exception as e:
            logger.warning(f"Firebase token validation failed: {e}. Falling back to demo mode headers.")

    # 2. Local Demo Mode: Role based on X-Demo-Role header
    role_str = (x_demo_role or "ADMIN").upper()
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.ADMIN

    return CurrentUser(
        uid="local-demo-user",
        email=f"{role.value.lower()}@cloudsentinel.local",
        role=role
    )


def require_role(min_role: UserRole):
    """
    Dependency checking user privilege against required role.
    Hierarchy: ADMIN > OPERATOR > VIEWER
    """
    role_levels = {
        UserRole.VIEWER: 1,
        UserRole.OPERATOR: 2,
        UserRole.ADMIN: 3
    }

    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        user_level = role_levels.get(current_user.role, 1)
        required_level = role_levels.get(min_role, 3)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires minimum role [{min_role.value}], but current role is [{current_user.role.value}]"
            )
        return current_user

    return role_checker
