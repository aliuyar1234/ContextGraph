from collections.abc import Generator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from ocg.core.security import AuthContext, build_auth_context, require_role
from ocg.core.settings import Settings, get_settings
from ocg.db.session import get_db_session


def get_settings_dep() -> Settings:
    return get_settings()


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_auth_context(
    settings: Settings = Depends(get_settings_dep),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_dev_user: str | None = Header(default=None, alias="X-Dev-User"),
    x_dev_role: str | None = Header(default=None, alias="X-Dev-Role"),
) -> AuthContext:
    return build_auth_context(
        settings=settings,
        authorization_header=authorization,
        dev_user=x_dev_user,
        dev_role=x_dev_role,
    )


def require_admin(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    require_role(context, {"admin"})
    return context


def require_analytics_role(
    context: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings_dep),
) -> AuthContext:
    allowed = {role.strip() for role in settings.analytics_viewer_roles.split(",") if role.strip()}
    require_role(context, allowed or {"analyst", "admin"})
    return context

