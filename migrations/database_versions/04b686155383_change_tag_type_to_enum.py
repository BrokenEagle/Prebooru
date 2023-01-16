# MIGRATIONS/VERSIONS/04B686155383_CHANGE_TAG_TYPE_TO_ENUM.PY
"""Change tag type to enum

Revision ID: 04b686155383
Revises: 4c29e207a0f9
Create Date: 2022-10-12 21:00:02.008786

"""

# ## PACKAGE IMPORTS
from migrations.columns import change_column_type


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '04b686155383'
down_revision = '4c29e207a0f9'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    from app.models.tag import TagType

    print("Changing type column from string to integer")
    for (value, update) in change_column_type('tag', 'type', 'String', 'Integer', 'INTEGER', False):
        enum_value = TagType[value].value
        update(**{'temp': enum_value})


def downgrade_():
    from app.models.tag import TagType

    print("Changing type column from integer to string")
    for (value, update) in change_column_type('tag', 'type', 'Integer', 'String', 'VARCHAR', False):
        enum_value = TagType(value).name
        update(**{'temp': enum_value})
