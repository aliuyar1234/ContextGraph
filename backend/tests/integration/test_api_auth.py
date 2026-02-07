from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ocg.api.deps import get_db
from ocg.core.settings import get_settings
from ocg.db.base import Base
from ocg.main import create_app


def _build_client() -> tuple[TestClient, sessionmaker]:
    get_settings.cache_clear()
    import os

    os.environ["OCG_AUTH_MODE"] = "oidc"
    os.environ["OCG_OIDC_ISSUER"] = "https://issuer.example.com"
    os.environ["OCG_OIDC_AUDIENCE"] = "ocg-api"
    os.environ["OCG_OIDC_HS256_SECRET"] = "test-secret"
    os.environ["OCG_SERVER_BIND"] = "127.0.0.1"

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    LocalSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    app = create_app()

    def _override_db():
        db = LocalSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), LocalSession


def _token(role: str) -> str:
    now = datetime.now(tz=UTC)
    payload = {
        "sub": "demo-user",
        "role": role,
        "email": "demo@example.com",
        "iss": "https://issuer.example.com",
        "aud": "ocg-api",
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_health_is_public():
    client, _ = _build_client()
    res = client.get("/healthz")
    assert res.status_code == 200


def test_auth_required_for_non_health():
    client, _ = _build_client()
    res = client.get("/api/v1/personal/timeline")
    assert res.status_code == 401


def test_admin_rbac_enforced():
    client, _ = _build_client()
    user_token = _token("user")
    admin_token = _token("admin")

    denied = client.get("/api/v1/admin/connectors", headers={"Authorization": f"Bearer {user_token}"})
    allowed = client.get("/api/v1/admin/connectors", headers={"Authorization": f"Bearer {admin_token}"})
    assert denied.status_code == 403
    assert allowed.status_code == 200
