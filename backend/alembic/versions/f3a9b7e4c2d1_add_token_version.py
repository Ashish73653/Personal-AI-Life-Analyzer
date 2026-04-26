"""add_token_version

Revision ID: f3a9b7e4c2d1
Revises: 61f8d9758961
Create Date: 2026-04-26 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a9b7e4c2d1'
down_revision: Union[str, Sequence[str], None] = '61f8d9758961'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('token_version', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('token_version')