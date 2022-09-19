"""Add indexes to many-to-one foreign keys

Revision ID: fd22b755387e
Revises: 650eb82244ee
Create Date: 2022-09-15 14:26:01.838020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd22b755387e'
down_revision = 'e0507dcd58c7'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('artist_url', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_artist_url_artist_id'), ['artist_id'], unique=False)

    with op.batch_alter_table('illust', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_illust_artist_id'), ['artist_id'], unique=False)

    with op.batch_alter_table('illust_url', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_illust_url_illust_id'), ['illust_id'], unique=False)

    with op.batch_alter_table('pool_element', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pool_element_illust_id'), ['illust_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pool_element_notation_id'), ['notation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pool_element_pool_id'), ['pool_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_pool_element_post_id'), ['post_id'], unique=False)

    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_similarity_pool_element_pool_id'), ['pool_id'], unique=False)

    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subscription_element_subscription_id'), ['subscription_id'], unique=False)

    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subscription_element_subscription_id'))

    with op.batch_alter_table('similarity_pool_element', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_similarity_pool_element_pool_id'))

    with op.batch_alter_table('pool_element', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pool_element_post_id'))
        batch_op.drop_index(batch_op.f('ix_pool_element_pool_id'))
        batch_op.drop_index(batch_op.f('ix_pool_element_notation_id'))
        batch_op.drop_index(batch_op.f('ix_pool_element_illust_id'))

    with op.batch_alter_table('illust_url', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_illust_url_illust_id'))

    with op.batch_alter_table('illust', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_illust_artist_id'))

    with op.batch_alter_table('artist_url', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_artist_url_artist_id'))

    # ### end Alembic commands ###

