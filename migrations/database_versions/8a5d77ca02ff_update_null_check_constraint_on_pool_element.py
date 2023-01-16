# MIGRATIONS/VERSIONS/8A5D77CA02FF_UPDATE_NULL_CHECK_CONSTRAINT_ON_POOL_ELEMENT.PY
"""Update null check constraint on pool_element

Revision ID: 8a5d77ca02ff
Revises: b311f123b313
Create Date: 2023-01-16 08:51:18.557347

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '8a5d77ca02ff'
down_revision = '3ae8bbe22ce7'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['pool_element'])
    drop_constraint('pool_element', 'ck_pool_element_ck_pool_element_null_check', 'check')
    create_constraint('pool_element', 'ck_pool_element_null_check', 'check', ["((post_id IS NULL) + (illust_id IS NULL) + (notation_id IS NULL)) = 2"])


def downgrade_():
    remove_temp_tables(['pool_element'])
    drop_constraint('pool_element', 'ck_pool_element_ck_pool_element_null_check', 'check')
    create_constraint('pool_element', 'ck_pool_element_null_check', 'check', ["post_id IS NOT NULL OR illust_id IS NOT NULL OR notation_id IS NOT NULL"])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

