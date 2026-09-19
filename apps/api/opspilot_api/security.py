from __future__ import annotations

from fastapi import Header, HTTPException, status

from .schemas import OrganizationContext, Role


def get_context(
    x_organization_id: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_role: str | None = Header(default=None),
) -> OrganizationContext:
    try:
        role = Role(x_role or Role.OPERATOR)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown role") from exc
    return OrganizationContext(
        organization_id=x_organization_id or "demo-org",
        user_id=x_user_id or "demo-operator",
        role=role,
    )


def require_write(context: OrganizationContext) -> OrganizationContext:
    if context.role == Role.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Viewer role is read-only"
        )
    return context
