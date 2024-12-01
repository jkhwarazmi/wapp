"""added db constraints

Revision ID: ce27229ca595
Revises: 0d1c95846291
Create Date: 2024-10-25 03:01:57.294934

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce27229ca595'
down_revision = '0d1c95846291'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assessment', schema=None) as batch_op:
        batch_op.alter_column('module',
               existing_type=sa.VARCHAR(length=10),
               nullable=False)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=False)
        batch_op.alter_column('modified_at',
               existing_type=sa.DATETIME(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('assessment', schema=None) as batch_op:
        batch_op.alter_column('modified_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('created_at',
               existing_type=sa.DATETIME(),
               nullable=True)
        batch_op.alter_column('title',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
        batch_op.alter_column('module',
               existing_type=sa.VARCHAR(length=10),
               nullable=True)

    # ### end Alembic commands ###
