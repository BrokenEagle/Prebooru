"""Add main boolean to similarity pool elements

Revision ID: 439e43f40fa4
Revises: d413db02c3e8
Create Date: 2022-07-14 17:55:03.385032

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '439e43f40fa4'
down_revision = 'd413db02c3e8'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


# Table definitions
t_similarity_pool_element = sa.Table(
    'similarity_pool_element',
    sa.MetaData(),
    sa.Column('id', sa.Integer),
    sa.Column('main', sa.Boolean),
)


def upgrade_():

    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('main', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###

    connection = op.get_bind()

    connection.execute(t_similarity_pool_element.update().values(
        main=False,
        ))

    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.alter_column('main',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.drop_column('main')

    # ### end Alembic commands ###

