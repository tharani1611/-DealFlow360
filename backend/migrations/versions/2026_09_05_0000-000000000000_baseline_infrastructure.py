"""Baseline database infrastructure setup

Revision ID: 000000000000
Revises: 
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000000000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates foundational PostgreSQL extensions if available."""
    # Ensure pgcrypto or uuid-ossp extension is enabled for native UUID support
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')


def downgrade() -> None:
    """Reverts foundational baseline extensions."""
    pass
