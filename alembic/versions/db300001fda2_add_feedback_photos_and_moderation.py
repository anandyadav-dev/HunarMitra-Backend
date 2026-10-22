"""add_feedback_photos_and_moderation

Revision ID: db300001fda2
Revises: ca200001bda1
Create Date: 2026-10-20 23:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'db300001fda2'
down_revision: Union[str, Sequence[str], None] = 'ca200001bda1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    existing_tables = insp.get_table_names()

    # 1. Add is_hidden column to feedbacks if missing
    if 'feedbacks' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('feedbacks')]
        if 'is_hidden' not in existing_cols:
            op.add_column('feedbacks', sa.Column('is_hidden', sa.Boolean(), server_default='0', nullable=False))
            op.create_index(op.f('ix_feedbacks_is_hidden'), 'feedbacks', ['is_hidden'], unique=False)

    # 2. Create feedback_photos table
    if 'feedback_photos' not in existing_tables:
        op.create_table(
            'feedback_photos',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('feedback_id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('photo_url', sa.String(length=500), nullable=False),
            sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
            sa.Column('rejection_reason', sa.String(length=255), nullable=True),
            sa.Column('reward_granted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('reward_coins', sa.Integer(), server_default='0', nullable=False),
            sa.Column('reviewed_by', sa.Uuid(), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['feedback_id'], ['feedbacks.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedback_photos_feedback_id'), 'feedback_photos', ['feedback_id'], unique=False)
        op.create_index(op.f('ix_feedback_photos_user_id'), 'feedback_photos', ['user_id'], unique=False)
        op.create_index(op.f('ix_feedback_photos_status'), 'feedback_photos', ['status'], unique=False)
        op.create_index(op.f('ix_feedback_photos_created_at'), 'feedback_photos', ['created_at'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    existing_tables = insp.get_table_names()

    if 'feedback_photos' in existing_tables:
        op.drop_table('feedback_photos')

    if 'feedbacks' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('feedbacks')]
        if 'is_hidden' in existing_cols:
            op.drop_index(op.f('ix_feedbacks_is_hidden'), table_name='feedbacks')
            op.drop_column('feedbacks', 'is_hidden')
