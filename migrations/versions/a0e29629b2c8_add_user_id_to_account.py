"""Add user_id to Account

Revision ID: a0e29629b2c8
Revises: 
Create Date: 2025-07-23 12:00:45.277018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column, table


# revision identifiers, used by Alembic.
revision: str = 'a0e29629b2c8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        # If there's existing data, set user_id to a valid user (e.g., 1)
        # batch_op.create_foreign_key('fk_account_user', 'user', ['user_id'], ['id'])
    # If you want to enforce NOT NULL, do it after setting all values
    # op.execute("UPDATE account SET user_id = 1")
    # with op.batch_alter_table('account', schema=None) as batch_op:
    #     batch_op.alter_column('user_id', nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('account', schema=None) as batch_op:
        batch_op.drop_column('user_id')
        # batch_op.drop_constraint('fk_account_user', type_='foreignkey')
