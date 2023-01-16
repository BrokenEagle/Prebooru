# MIGRATIONS/VERSIONS/1628B38AAE0A_CHANGE_INDEXES_ON_POOL_ELEMENT.PY
"""Change indexes on pool_element

Revision ID: 1628b38aae0a
Revises: 92272e95643a
Create Date: 2022-10-17 14:11:57.575056

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_indexes, drop_indexes


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '1628b38aae0a'
down_revision = '92272e95643a'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['pool_element'])
    create_constraint('pool_element', 'ck_duplicate_post_null_check', 'check', "post_id IS NOT NULL OR illust_id IS NOT NULL OR notation_id IS NOT NULL")
    # WARNING: Partial indexes need to be changed last, since batch operations seem to wipe out the where clauses
    create_indexes('pool_element', [
        ('ix_pool_element_illust_id_pool_id', ['illust_id', 'pool_id'], True, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_pool_element_notation_id_pool_id', ['notation_id', 'pool_id'], True, {'sqlite_where': 'notation_id IS NOT NULL'}),
        ('ix_pool_element_post_id_pool_id', ['post_id', 'pool_id'], True, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])
    drop_indexes('pool_element', ['ix_pool_element_illust_id', 'ix_pool_element_notation_id', 'ix_pool_element_post_id'])


def downgrade_():
    remove_temp_tables(['pool_element'])
    drop_constraint('pool_element', 'ck_duplicate_post_null_check', 'check')
    drop_indexes('pool_element', ['ix_pool_element_illust_id_pool_id', 'ix_pool_element_notation_id_pool_id', 'ix_pool_element_post_id_pool_id'])
    create_indexes('pool_element', [
        ('ix_pool_element_illust_id', ['illust_id'], False),
        ('ix_pool_element_notation_id', ['notation_id'], False),
        ('ix_pool_element_post_id', ['post_id'], False),
    ])
