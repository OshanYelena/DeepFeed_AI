"""Initial schema: all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-06-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # ── user_profiles ─────────────────────────────────────────────────────────
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expertise_level', sa.String(20), nullable=False, server_default='intermediate'),
        sa.Column('preferred_depth', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('preferred_frequency', sa.String(20), nullable=False, server_default='daily'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # ── interests ─────────────────────────────────────────────────────────────
    op.create_table(
        'interests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── sources ───────────────────────────────────────────────────────────────
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=False),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── content_items ─────────────────────────────────────────────────────────
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('canonical_url', sa.Text(), nullable=True),
        sa.Column('author', sa.Text(), nullable=True),
        sa.Column('published_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('discovered_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False, server_default='article'),
        sa.Column('status', sa.String(50), nullable=False, server_default='discovered'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_url'),
    )
    op.create_index('idx_content_items_canonical_url', 'content_items', ['canonical_url'])
    op.create_index('idx_content_items_source_id', 'content_items', ['source_id'])
    op.create_index('idx_content_items_status', 'content_items', ['status'])

    # ── processed_contents ────────────────────────────────────────────────────
    op.create_table(
        'processed_contents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clean_text', sa.Text(), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('extraction_quality', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_item_id'),
    )

    # ── content_topics ────────────────────────────────────────────────────────
    op.create_table(
        'content_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_name', sa.String(255), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── recommendations ───────────────────────────────────────────────────────
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('freshness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('credibility_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('novelty_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('final_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rank_position', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_recommendations_user_id', 'recommendations', ['user_id'])
    op.create_index('idx_recommendations_final_score', 'recommendations', ['final_score'], postgresql_ops={'final_score': 'DESC'})

    # ── recommendation_traces ─────────────────────────────────────────────────
    op.create_table(
        'recommendation_traces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('matched_interests', postgresql.JSONB(), nullable=True),
        sa.Column('scoring_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('recommendation_id'),
    )

    # ── summaries ─────────────────────────────────────────────────────────────
    op.create_table(
        'summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_short', sa.Text(), nullable=True),
        sa.Column('summary_detailed', sa.Text(), nullable=True),
        sa.Column('key_takeaways', postgresql.JSONB(), nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=False, server_default='fallback'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_item_id'),
    )

    # ── feedback ──────────────────────────────────────────────────────────────
    op.create_table(
        'feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('feedback_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_feedback_user_id', 'feedback', ['user_id'])

    # ── user_interest_signals ─────────────────────────────────────────────────
    op.create_table(
        'user_interest_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signal_type', sa.String(50), nullable=False),
        sa.Column('signal_strength', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── user_topic_preferences ────────────────────────────────────────────────
    op.create_table(
        'user_topic_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('source', sa.String(50), nullable=False, server_default='explicit'),
        sa.Column('first_detected_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'topic', name='uq_user_topic'),
    )
    op.create_index('idx_user_topic_preferences_user_id', 'user_topic_preferences', ['user_id'])

    # ── source_preferences ────────────────────────────────────────────────────
    op.create_table(
        'source_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('personal_trust_score', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('interaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('positive_feedback_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('negative_feedback_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'source_id', name='uq_user_source'),
    )

    # ── search_plans ──────────────────────────────────────────────────────────
    op.create_table(
        'search_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_by', sa.String(100), nullable=False),
        sa.Column('queries', postgresql.JSONB(), nullable=False),
        sa.Column('source_priorities', postgresql.JSONB(), nullable=True),
        sa.Column('search_depth', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_search_plans_user_id', 'search_plans', ['user_id'])

    # ── adaptation_events ─────────────────────────────────────────────────────
    op.create_table(
        'adaptation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('input_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('decision', postgresql.JSONB(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_adaptation_events_user_id', 'adaptation_events', ['user_id'])

    # ── reflection_reports ────────────────────────────────────────────────────
    op.create_table(
        'reflection_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_period', sa.String(20), nullable=False),
        sa.Column('insights', postgresql.JSONB(), nullable=False),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('reflection_reports')
    op.drop_table('adaptation_events')
    op.drop_table('search_plans')
    op.drop_table('source_preferences')
    op.drop_table('user_topic_preferences')
    op.drop_table('user_interest_signals')
    op.drop_table('feedback')
    op.drop_table('summaries')
    op.drop_table('recommendation_traces')
    op.drop_table('recommendations')
    op.drop_table('content_topics')
    op.drop_table('processed_contents')
    op.drop_table('content_items')
    op.drop_table('sources')
    op.drop_table('interests')
    op.drop_table('user_profiles')
    op.drop_table('users')
