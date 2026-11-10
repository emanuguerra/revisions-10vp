"""training sessions and answers kept for review

Revision ID: 7c1e2a9d4b10
Revises: 4231b6cfdf0b
Create Date: 2026-11-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c1e2a9d4b10'
down_revision: Union[str, Sequence[str], None] = '4231b6cfdf0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('missions') as batch:
        batch.add_column(sa.Column('mode', sa.String(length=16), nullable=False, server_default='mission'))
    with op.batch_alter_table('questions') as batch:
        batch.add_column(sa.Column('answers', sa.JSON(), nullable=False, server_default='[]'))


def downgrade() -> None:
    with op.batch_alter_table('questions') as batch:
        batch.drop_column('answers')
    with op.batch_alter_table('missions') as batch:
        batch.drop_column('mode')
