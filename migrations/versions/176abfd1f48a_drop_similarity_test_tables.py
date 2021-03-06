"""Drop similarity test tables

Revision ID: 176abfd1f48a
Revises: b146a6975923
Create Date: 2021-07-30 00:39:16.286957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '176abfd1f48a'
down_revision = 'b146a6975923'
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
    op.drop_table('similarity_result2')
    op.drop_table('similarity_result3')
    # ### end Alembic commands ###


def downgrade_similarity():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('similarity_result3',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('post_id', sa.INTEGER(), nullable=False),
    sa.Column('chunk00', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk01', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk02', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk03', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk04', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk05', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk06', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk07', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk08', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk09', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk10', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk11', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk12', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk13', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk14', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk15', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk16', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk17', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk18', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk19', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk20', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk21', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk22', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk23', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk24', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk25', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk26', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk27', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk28', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk29', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk30', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk31', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk32', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk33', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk34', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk35', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk36', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk37', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk38', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk39', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk40', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk41', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk42', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk43', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk44', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk45', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk46', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk47', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk48', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk49', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk50', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk51', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk52', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk53', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk54', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk55', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk56', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk57', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk58', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk59', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk60', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk61', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk62', sa.VARCHAR(length=1), nullable=False),
    sa.Column('chunk63', sa.VARCHAR(length=1), nullable=False),
    sa.PrimaryKeyConstraint('id', name='pk_similarity_result3')
    )
    op.create_table('similarity_result2',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('post_id', sa.INTEGER(), nullable=False),
    sa.Column('chunk00', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk01', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk02', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk03', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk04', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk05', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk06', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk07', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk08', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk09', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk10', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk11', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk12', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk13', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk14', sa.VARCHAR(length=2), nullable=False),
    sa.Column('chunk15', sa.VARCHAR(length=2), nullable=False),
    sa.PrimaryKeyConstraint('id', name='pk_similarity_result2')
    )
    # ### end Alembic commands ###

