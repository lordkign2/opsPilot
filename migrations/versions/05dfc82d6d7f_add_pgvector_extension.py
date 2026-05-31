"""add pgvector extension

Revision ID: 05dfc82d6d7f
Revises: 3e43bf6a651f
Create Date: 2026-05-31 23:49:24.587503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05dfc82d6d7f'
down_revision: Union[str, None] = '3e43bf6a651f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS vector;')
