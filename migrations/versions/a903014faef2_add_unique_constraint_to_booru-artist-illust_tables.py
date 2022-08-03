"""Add unique constraint to booru/artist/illust tables

Revision ID: a903014faef2
Revises: 1165a7fef786
Create Date: 2022-08-03 12:29:37.910767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a903014faef2'
down_revision = '1165a7fef786'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    print("Adding booru unique constraint.")
    with op.batch_alter_table('booru', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_booru_danbooru_id', ['danbooru_id'])

    print("Adding artist unique constraint.")
    with op.batch_alter_table('artist', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_artist_site_id'), ['site_id', 'site_artist_id'])

    print("Adding illust unique constraint.")
    with op.batch_alter_table('illust', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_illust_site_id'), ['site_id', 'site_illust_id'])

    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    print("Dropping illust unique constraint.")
    with op.batch_alter_table('illust', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_illust_site_id'), type_='unique')

    print("Dropping artist unique constraint.")
    with op.batch_alter_table('artist', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_artist_site_id'), type_='unique')

    print("Dropping booru unique constraint.")
    with op.batch_alter_table('booru', schema=None) as batch_op:
        batch_op.drop_constraint('uq_booru_danbooru_id', type_='unique')

    # ### end Alembic commands ###

