"""add_query_history

Revision ID: 61f8d9758961
Revises: 786842c29470
Create Date: 2026-04-26 11:35:37.739997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61f8d9758961'
down_revision: Union[str, Sequence[str], None] = '786842c29470'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'query_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('asked_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('query_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_query_history_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('query_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_query_history_user_id'))

    op.drop_table('query_history')
