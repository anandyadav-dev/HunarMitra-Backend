"""phase_1_coins_and_wallet_foundation

Revision ID: 23e8435291f0
Revises: 
Create Date: 2026-10-20 23:17:17.054464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '23e8435291f0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    existing_tables = insp.get_table_names()

    # 1. Update wallets table with coin columns if they don't already exist
    if 'wallets' in existing_tables:
        existing_cols = [c['name'] for c in insp.get_columns('wallets')]
        if 'purchased_coins' not in existing_cols:
            op.add_column('wallets', sa.Column('purchased_coins', sa.Integer(), server_default='0', nullable=False))
        if 'earned_coins' not in existing_cols:
            op.add_column('wallets', sa.Column('earned_coins', sa.Integer(), server_default='0', nullable=False))

    # 2. Create coin_packs table
    if 'coin_packs' not in existing_tables:
        op.create_table(
            'coin_packs',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('code', sa.String(length=50), nullable=False),
            sa.Column('coins', sa.Integer(), nullable=False),
            sa.Column('bonus_coins', sa.Integer(), server_default='0', nullable=False),
            sa.Column('price_inr', sa.DECIMAL(precision=10, scale=2), nullable=False),
            sa.Column('is_popular', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('badge_text', sa.String(length=50), nullable=True),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_coin_packs_code'), 'coin_packs', ['code'], unique=True)

    # 3. Create coin_ledgers table
    if 'coin_ledgers' not in existing_tables:
        op.create_table(
            'coin_ledgers',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('wallet_id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('action', sa.String(length=20), nullable=False),
            sa.Column('coin_type', sa.String(length=20), nullable=False),
            sa.Column('transaction_type', sa.String(length=50), nullable=False),
            sa.Column('balance_purchased_after', sa.Integer(), server_default='0', nullable=False),
            sa.Column('balance_earned_after', sa.Integer(), server_default='0', nullable=False),
            sa.Column('balance_total_after', sa.Integer(), server_default='0', nullable=False),
            sa.Column('reference_id', sa.String(length=255), nullable=True),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_coin_ledgers_created_at'), 'coin_ledgers', ['created_at'], unique=False)
        op.create_index(op.f('ix_coin_ledgers_reference_id'), 'coin_ledgers', ['reference_id'], unique=False)
        op.create_index(op.f('ix_coin_ledgers_transaction_type'), 'coin_ledgers', ['transaction_type'], unique=False)
        op.create_index(op.f('ix_coin_ledgers_user_id'), 'coin_ledgers', ['user_id'], unique=False)
        op.create_index(op.f('ix_coin_ledgers_wallet_id'), 'coin_ledgers', ['wallet_id'], unique=False)

    # 4. Create engagements table
    if 'engagements' not in existing_tables:
        op.create_table(
            'engagements',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('worker_id', sa.Uuid(), nullable=False),
            sa.Column('engagement_type', sa.String(length=50), server_default='CONTACT_UNLOCK', nullable=False),
            sa.Column('coins_spent', sa.Integer(), server_default='0', nullable=False),
            sa.Column('purchased_coins_spent', sa.Integer(), server_default='0', nullable=False),
            sa.Column('earned_coins_spent', sa.Integer(), server_default='0', nullable=False),
            sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
            sa.Column('contact_phone', sa.String(length=20), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_engagements_user_id'), 'engagements', ['user_id'], unique=False)
        op.create_index(op.f('ix_engagements_worker_id'), 'engagements', ['worker_id'], unique=False)

    # 5. Create feedbacks table
    if 'feedbacks' not in existing_tables:
        op.create_table(
            'feedbacks',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('engagement_id', sa.Uuid(), nullable=True),
            sa.Column('worker_id', sa.Uuid(), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('category', sa.String(length=50), server_default='WORKER_EXPERIENCE', nullable=False),
            sa.Column('comments', sa.Text(), nullable=True),
            sa.Column('reward_granted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('reward_coins', sa.Integer(), server_default='0', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedbacks_engagement_id'), 'feedbacks', ['engagement_id'], unique=False)
        op.create_index(op.f('ix_feedbacks_user_id'), 'feedbacks', ['user_id'], unique=False)
        op.create_index(op.f('ix_feedbacks_worker_id'), 'feedbacks', ['worker_id'], unique=False)

    # 6. Create rewards table
    if 'rewards' not in existing_tables:
        op.create_table(
            'rewards',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('reward_code', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('coins_amount', sa.Integer(), nullable=False),
            sa.Column('max_claims_per_user', sa.Integer(), server_default='1', nullable=False),
            sa.Column('valid_until', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_rewards_reward_code'), 'rewards', ['reward_code'], unique=True)

    # 7. Create user_rewards table
    if 'user_rewards' not in existing_tables:
        op.create_table(
            'user_rewards',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('reward_id', sa.Uuid(), nullable=True),
            sa.Column('reward_code', sa.String(length=50), nullable=False),
            sa.Column('coins_awarded', sa.Integer(), nullable=False),
            sa.Column('reference_id', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_rewards_reward_code'), 'user_rewards', ['reward_code'], unique=False)
        op.create_index(op.f('ix_user_rewards_reward_id'), 'user_rewards', ['reward_id'], unique=False)
        op.create_index(op.f('ix_user_rewards_user_id'), 'user_rewards', ['user_id'], unique=False)

    # 8. Create system_configs table
    if 'system_configs' not in existing_tables:
        op.create_table(
            'system_configs',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('value_type', sa.String(length=20), server_default='string', nullable=False),
            sa.Column('category', sa.String(length=50), server_default='coins', nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_public', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_system_configs_category'), 'system_configs', ['category'], unique=False)
        op.create_index(op.f('ix_system_configs_key'), 'system_configs', ['key'], unique=True)


def downgrade() -> None:
    op.drop_table('system_configs')
    op.drop_table('user_rewards')
    op.drop_table('rewards')
    op.drop_table('feedbacks')
    op.drop_table('engagements')
    op.drop_table('coin_ledgers')
    op.drop_table('coin_packs')
    op.drop_column('wallets', 'earned_coins')
    op.drop_column('wallets', 'purchased_coins')
