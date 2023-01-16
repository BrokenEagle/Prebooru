# MIGRATIONS/VERSIONS/4C29E207A0F9_CHANGE_POOL_ELEMENT_TYPE_TO_ENUM.PY
"""Change pool element type to enum

Revision ID: 4c29e207a0f9
Revises: 0d7ddfdeb870
Create Date: 2022-10-12 16:30:46.827197

"""

# ## PACKAGE IMPORTS
from migrations.columns import change_column_type


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '4c29e207a0f9'
down_revision = '0d7ddfdeb870'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    from app.models.pool_element import PoolElementType

    print("Changing type column from string to integer")
    for (value, update) in change_column_type('pool_element', 'type', 'String', 'Integer', 'INTEGER', False):
        enum_value = PoolElementType[value].value
        update(**{'temp': enum_value})


def downgrade_():
    from app.models.pool_element import PoolElementType

    print("Changing type column from integer to string")
    for (value, update) in change_column_type('pool_element', 'type', 'Integer', 'String', 'VARCHAR', False):
        enum_value = PoolElementType(value).name
        update(**{'temp': enum_value})
