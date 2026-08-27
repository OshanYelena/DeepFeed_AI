"""Add discovery_runs table for manual on-demand discovery

Revision ID: 002_discovery_runs
Revises: 001_initial
Create Date: 2026-06-09 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '002_discovery_runs'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'discovery_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('trigger_type', sa.String(32), nullable=False, server_default='personalized'),
        sa.Column('search_queries', postgresql.JSONB, nullable=True),
        sa.Column('new_items_count', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_discovery_runs_user_started',
        'discovery_runs',
        ['user_id', 'started_at'],
    )
    op.create_index(
        'idx_discovery_runs_status',
        'discovery_runs',
        ['status'],
    )
    op.create_index(
        'ix_discovery_runs_task_id',
        'discovery_runs',
        ['task_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_discovery_runs_task_id', table_name='discovery_runs')
    op.drop_index('idx_discovery_runs_status', table_name='discovery_runs')
    op.drop_index('idx_discovery_runs_user_started', table_name='discovery_runs')
    op.drop_table('discovery_runs')
