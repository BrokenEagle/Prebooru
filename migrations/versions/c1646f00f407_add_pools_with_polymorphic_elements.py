"""Add pools with polymorphic elements

Revision ID: c1646f00f407
Revises: b08b2788d5cd
Create Date: 2021-05-28 13:11:07.008519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1646f00f407'
down_revision = 'b08b2788d5cd'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pool',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pool'))
    )
    op.create_table('pool_element',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pool_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('illust_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['illust_id'], ['illust.id'], name=op.f('fk_pool_element_illust_id_illust')),
    sa.ForeignKeyConstraint(['pool_id'], ['pool.id'], name=op.f('fk_pool_element_pool_id_pool')),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], name=op.f('fk_pool_element_post_id_post')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pool_element'))
    )
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pool_element')
    op.drop_table('pool')
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

