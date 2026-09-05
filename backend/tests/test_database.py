import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base, UUIDMixin, TimestampMixin, check_database_connection, POSTGRES_NAMING_CONVENTION
from migrations.env import target_metadata


class DummyTestModel(Base, UUIDMixin, TimestampMixin):
    """Test entity inheriting base mixins without being mapped to business domain."""
    __tablename__ = "dummy_test_table"
    name: Mapped[str] = mapped_column(nullable=False)


def test_naming_conventions_configured():
    """Verify PostgreSQL naming convention dictionary is registered on Base metadata."""
    assert Base.metadata.naming_convention == POSTGRES_NAMING_CONVENTION
    assert Base.metadata.naming_convention["pk"] == "pk_%(table_name)s"
    assert Base.metadata.naming_convention["fk"] == "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"


def test_uuid_and_timestamp_mixins_schema():
    """Verify UUIDMixin and TimestampMixin table schema column definitions."""
    table = DummyTestModel.__table__
    assert "id" in table.columns
    assert "created_at" in table.columns
    assert "updated_at" in table.columns
    
    id_col = table.columns["id"]
    assert id_col.primary_key is True
    
    # Verify model instantiation with explicit UUID
    test_id = uuid.uuid4()
    instance = DummyTestModel(id=test_id, name="Test Item")
    assert instance.id == test_id
    assert instance.name == "Test Item"


def test_alembic_metadata_target():
    """Verify Alembic target_metadata is bound to Base.metadata."""
    assert target_metadata is Base.metadata


@pytest.mark.asyncio
async def test_database_connection_check():
    """Verify check_database_connection executes and returns a boolean value."""
    res = await check_database_connection()
    assert isinstance(res, bool)
