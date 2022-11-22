# MIGRATIONS/VERSIONS/F1E2A6875B1E_ADD_ENUM_TABLES.PY
"""Add enum tables

Revision ID: f1e2a6875b1e
Revises: 754d9b6b1460
Create Date: 2022-11-22 13:48:19.932642

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'f1e2a6875b1e'
down_revision = '754d9b6b1460'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table('api_data_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_api_data_type'))
    )
    op.create_table('archive_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_archive_type'))
    )
    op.create_table('pool_element_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pool_element_type'))
    )
    op.create_table('post_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_post_type'))
    )
    op.create_table('site_data_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_site_data_type'))
    )
    op.create_table('site_descriptor',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_site_descriptor'))
    )
    op.create_table('subscription_element_keep',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_subscription_element_keep'))
    )
    op.create_table('subscription_element_status',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_subscription_element_type'))
    )
    op.create_table('subscription_status',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_subscription_status'))
    )
    op.create_table('tag_type',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_tag_type'))
    )
    op.create_table('upload_element_status',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_upload_element_status'))
    )
    op.create_table('upload_status',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_upload_status'))
    )


def downgrade_():
    op.drop_table('upload_status')
    op.drop_table('upload_element_status')
    op.drop_table('tag_type')
    op.drop_table('subscription_status')
    op.drop_table('subscription_element_status')
    op.drop_table('subscription_element_keep')
    op.drop_table('site_descriptor')
    op.drop_table('site_data_type')
    op.drop_table('post_type')
    op.drop_table('pool_element_type')
    op.drop_table('archive_type')
    op.drop_table('api_data_type')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
