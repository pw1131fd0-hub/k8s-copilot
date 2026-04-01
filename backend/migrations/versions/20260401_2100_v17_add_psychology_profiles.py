"""add psychology_profiles table for v1.7 AI Psychology Module

Revision ID: v17_add_psychology_profiles
Revises: v17_add_sentiment_score
Create Date: 2026-04-01 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "v17_add_psychology_profiles"
down_revision: Union[str, None] = "v17_add_sentiment_score"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create psychology_profiles table for v1.7 personality assessment feature."""
    op.create_table(
        'psychology_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('traits_data', sa.Text(), nullable=False),
        sa.Column('archetype', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=False),
        sa.Column('insights_data', sa.Text(), nullable=True),
        sa.Column('posts_analyzed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_psychology_profiles_created_at', 'psychology_profiles', ['created_at'])


def downgrade() -> None:
    """Drop psychology_profiles table."""
    op.drop_index('ix_psychology_profiles_created_at', table_name='psychology_profiles')
    op.drop_table('psychology_profiles')
