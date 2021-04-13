"""Add sibling ID to similarity pool element

Revision ID: b146a6975923
Revises: 0e3fb2605efd
Create Date: 2021-07-26 00:32:17.704738

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b146a6975923'
down_revision = '0e3fb2605efd'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
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
    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sibling_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_similarity_pool_element_sibling_id_similarity_pool_element'), 'similarity_pool_element', ['sibling_id'], ['id'])

    # ### end Alembic commands ###


def downgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_similarity_pool_element_sibling_id_similarity_pool_element'), type_='foreignkey')
        batch_op.drop_column('sibling_id')

    # ### end Alembic commands ###

