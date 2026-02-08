from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

import jwt
from fastapi import HTTPException, status

from ocg.core.observability import AUTH_FAILURES
from ocg.core.settings import Settings


@dataclass(frozen=True)
class AuthContext:
    person_id: str
    principal_ids: list[str]
    role: str
    email_hash: str


def validate_startup_security(settings: Settings) -> None:
    local_binds = {"127.0.0.1", "localhost", "::1"}
    if settings.server_bind not in local_binds:
        if settings.auth_mode != "oidc":
            raise RuntimeError("AUTH_MODE must be oidc when SERVER_BIND is non-local.")
        missing = [
            key
            for key, value in {
                "OIDC_ISSUER": settings.oidc_issuer,
                "OIDC_AUDIENCE": settings.oidc_audience,
                "OIDC_HS256_SECRET": settings.oidc_hs256_secret,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Public bind requires OIDC config. Missing: " + ", ".join(sorted(missing))
            )


def _decode_oidc_token(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.oidc_hs256_secret or not settings.oidc_audience or not settings.oidc_issuer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC is not fully configured.",
        )
    try:
        payload = jwt.decode(
            token,
            settings.oidc_hs256_secret,
            algorithms=["HS256"],
            audience=settings.oidc_audience,
            issuer=settings.oidc_issuer,
            leeway=settings.jwt_clock_skew_seconds,
        )
    except jwt.PyJWTError as exc:
        AUTH_FAILURES.inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        ) from exc
    return payload


def build_auth_context(
    *,
    settings: Settings,
    authorization_header: str | None,
    dev_user: str | None,
    dev_role: str | None,
) -> AuthContext:
    if settings.dev_auth_enabled:
        person_id = dev_user or "demo-user"
        role = dev_role or "admin"
        principal_ids = [person_id, f"group:{role}"]
        return AuthContext(
            person_id=person_id,
            principal_ids=principal_ids,
            role=role,
            email_hash=sha256(f"{person_id}@dev.local".encode("utf-8")).hexdigest(),
        )

    if not authorization_header or not authorization_header.lower().startswith("bearer "):
        AUTH_FAILURES.inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token."
        )
    token = authorization_header.split(" ", 1)[1].strip()
    payload = _decode_oidc_token(token, settings)
    now = datetime.now(tz=UTC).timestamp()
    if "exp" in payload and float(payload["exp"]) < now - settings.jwt_clock_skew_seconds:
        AUTH_FAILURES.inc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired.")

    person_id = str(payload.get("sub", "")).strip()
    if not person_id:
        AUTH_FAILURES.inc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject.")

    role = str(payload.get("role", "user")).strip().lower()
    groups = payload.get("groups", [])
    principal_ids = [person_id]
    if isinstance(groups, list):
        principal_ids.extend([f"group:{g}" for g in groups if g])
    principal_ids.append(f"group:{role}")
    email = str(payload.get("email", f"{person_id}@unknown.local"))
    return AuthContext(
        person_id=person_id,
        principal_ids=sorted(set(principal_ids)),
        role=role,
        email_hash=sha256(email.encode("utf-8")).hexdigest(),
    )


def require_role(context: AuthContext, allowed_roles: set[str]) -> None:
    if context.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
