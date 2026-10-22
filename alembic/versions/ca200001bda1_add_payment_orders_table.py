"""add_payment_orders_table

Revision ID: ca200001bda1
Revises: 23e8435291f0
Create Date: 2026-10-20 23:36:51.820909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'ca200001bda1'
down_revision: Union[str, Sequence[str], None] = '23e8435291f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    existing_tables = insp.get_table_names()

    if 'payment_orders' not in existing_tables:
        op.create_table(
            'payment_orders',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
            sa.Column('order_id', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('pack_id', sa.Uuid(), nullable=True),
            sa.Column('pack_name', sa.String(length=100), nullable=False),
            sa.Column('pack_code', sa.String(length=50), nullable=False),
            sa.Column('coins', sa.Integer(), nullable=False),
            sa.Column('bonus_coins', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_coins', sa.Integer(), nullable=False),
            sa.Column('amount_inr', sa.DECIMAL(precision=10, scale=2), nullable=False),
            sa.Column('currency', sa.String(length=10), server_default='INR', nullable=False),
            sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
            sa.Column('payment_method', sa.String(length=50), nullable=True),
            sa.Column('gateway_order_id', sa.String(length=100), nullable=True),
            sa.Column('gateway_payment_id', sa.String(length=100), nullable=True),
            sa.Column('gateway_signature', sa.String(length=255), nullable=True),
            sa.Column('coins_credited', sa.Boolean(), server_default='0', nullable=False),
            sa.Column('credited_at', sa.DateTime(), nullable=True),
            sa.Column('failure_reason', sa.String(length=255), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['pack_id'], ['coin_packs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_payment_orders_created_at'), 'payment_orders', ['created_at'], unique=False)
        op.create_index(op.f('ix_payment_orders_gateway_order_id'), 'payment_orders', ['gateway_order_id'], unique=False)
        op.create_index(op.f('ix_payment_orders_gateway_payment_id'), 'payment_orders', ['gateway_payment_id'], unique=False)
        op.create_index(op.f('ix_payment_orders_order_id'), 'payment_orders', ['order_id'], unique=True)
        op.create_index(op.f('ix_payment_orders_pack_id'), 'payment_orders', ['pack_id'], unique=False)
        op.create_index(op.f('ix_payment_orders_status'), 'payment_orders', ['status'], unique=False)
        op.create_index(op.f('ix_payment_orders_user_id'), 'payment_orders', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('payment_orders')
