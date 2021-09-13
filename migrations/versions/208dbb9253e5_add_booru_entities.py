"""Add booru entities

Revision ID: 208dbb9253e5
Revises: 0364657a86ca
Create Date: 2021-06-27 12:14:10.365352

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '208dbb9253e5'
down_revision = '0364657a86ca'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('booru',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('danbooru_id', sa.Integer(), nullable=False),
    sa.Column('current_name', sa.String(length=255), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_booru'))
    )
    op.create_table('booru_artists',
    sa.Column('artist_id', sa.Integer(), nullable=False),
    sa.Column('booru_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['artist.id'], name=op.f('fk_booru_artists_artist_id_artist')),
    sa.ForeignKeyConstraint(['booru_id'], ['booru.id'], name=op.f('fk_booru_artists_booru_id_booru')),
    sa.PrimaryKeyConstraint('artist_id', 'booru_id', name=op.f('pk_booru_artists'))
    )
    op.create_table('booru_names',
    sa.Column('label_id', sa.Integer(), nullable=False),
    sa.Column('booru_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['booru_id'], ['booru.id'], name=op.f('fk_booru_names_booru_id_booru')),
    sa.ForeignKeyConstraint(['label_id'], ['label.id'], name=op.f('fk_booru_names_label_id_label')),
    sa.PrimaryKeyConstraint('label_id', 'booru_id', name=op.f('pk_booru_names'))
    )
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('booru_names')
    op.drop_table('booru_artists')
    op.drop_table('booru')
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
