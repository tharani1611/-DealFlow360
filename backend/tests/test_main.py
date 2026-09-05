import pytest
from app.main import app
from app.core.config import settings


def test_app_imports_successfully():
    """Verify that the FastAPI application initializes without error."""
    assert app is not None
    assert app.title == settings.APP_NAME


def test_config_loads_correctly():
    """Verify application configuration parameters."""
    assert settings.API_V1_STR == "/api/v1"
    assert settings.PORT == 8000
    assert isinstance(settings.CORS_ORIGINS, list)
