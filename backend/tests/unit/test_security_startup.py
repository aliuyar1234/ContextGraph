import pytest

from ocg.core.security import validate_startup_security
from ocg.core.settings import Settings


def test_public_bind_requires_oidc_config():
    settings = Settings(
        server_bind="0.0.0.0",
        auth_mode="oidc",
        oidc_issuer=None,
        oidc_audience=None,
        oidc_hs256_secret=None,
    )
    with pytest.raises(RuntimeError):
        validate_startup_security(settings)


def test_local_bind_allows_missing_oidc():
    settings = Settings(server_bind="127.0.0.1", auth_mode="oidc")
    validate_startup_security(settings)

