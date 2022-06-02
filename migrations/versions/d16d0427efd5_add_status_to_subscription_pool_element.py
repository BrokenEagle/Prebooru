"""Add status to subscription pool element

Revision ID: d16d0427efd5
Revises: be785ee97783
Create Date: 2022-04-29 09:52:22.623065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd16d0427efd5'
down_revision = 'be785ee97783'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subscription_pool_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=16), nullable=True))

    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subscription_pool_element', schema=None) as batch_op:
        batch_op.drop_column('status')

    # ### end Alembic commands ###
