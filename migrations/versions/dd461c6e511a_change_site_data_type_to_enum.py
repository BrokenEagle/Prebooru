# MIGRATIONS/VERSIONS/DD461C6E511A_CHANGE_SITE_DATA_TYPE_TO_ENUM.PY
"""Change site data type to enum

Revision ID: dd461c6e511a
Revises: 04b686155383
Create Date: 2022-10-12 21:31:31.924784

"""

# ## PACKAGE IMPORTS
from migrations.columns import change_column_type


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'dd461c6e511a'
down_revision = '04b686155383'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    from app.models.site_data import SiteDataType

    print("Changing type column from string to integer")
    for (value, update) in change_column_type('site_data', 'type', 'String', 'Integer', 'INTEGER', False):
        enum_value = SiteDataType[value].value
        update(**{'temp': enum_value})


def downgrade_():
    from app.models.site_data import SiteDataType

    print("Changing type column from integer to string")
    for (value, update) in change_column_type('site_data', 'type', 'Integer', 'String', 'VARCHAR', False):
        enum_value = SiteDataType(value).name
        update(**{'temp': enum_value})
