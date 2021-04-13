"""Add notations table

Revision ID: 15a949a632cb
Revises: c1646f00f407
Create Date: 2021-05-28 14:14:12.312320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15a949a632cb'
down_revision = 'c1646f00f407'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('notation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.UnicodeText(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notation'))
    )
    with op.batch_alter_table('pool_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notation_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_pool_element_notation_id_notation'), 'notation', ['notation_id'], ['id'])

    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('pool_element', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_pool_element_notation_id_notation'), type_='foreignkey')
        batch_op.drop_column('notation_id')

    op.drop_table('notation')
    # ### end Alembic commands ###


def upgrade_cache():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_cache():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###

