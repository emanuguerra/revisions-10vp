"""focus sessions for the rewards

Revision ID: 9d3f6b2c1e07
Revises: 7c1e2a9d4b10
Create Date: 2026-11-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9d3f6b2c1e07'
down_revision: Union[str, Sequence[str], None] = '7c1e2a9d4b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'focus_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_focus_sessions_profile_id', 'focus_sessions', ['profile_id'])


def downgrade() -> None:
    op.drop_index('ix_focus_sessions_profile_id', table_name='focus_sessions')
    op.drop_table('focus_sessions')
