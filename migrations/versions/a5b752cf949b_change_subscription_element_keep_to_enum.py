# MIGRATIONS/VERSIONS/A5B752CF949B_CHANGE_SUBSCRIPTION_ELEMENT_KEEP_TO_ENUM.PY
"""Change Subscription Element keep to enum

Revision ID: a5b752cf949b
Revises: 14b5387b0456
Create Date: 2022-09-30 16:00:21.486231

"""

# ## PACKAGE IMPORTS
from migrations.columns import change_column_type


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'a5b752cf949b'
down_revision = '14b5387b0456'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    from app.models.subscription_element import SubscriptionElementKeep

    print("Changing keep column from string to integer")
    for (value, update) in change_column_type('subscription_element', 'keep', 'String', 'Integer', 'INTEGER', True):
        enum_value = SubscriptionElementKeep[value].value if value is not None else None
        update(**{'temp': enum_value})


def downgrade_():
    from app.models.subscription_element import SubscriptionElementKeep

    print("Changing keep column from integer to string")
    for (value, update) in change_column_type('subscription_element', 'keep', 'Integer', 'String', 'VARCHAR', True):
        enum_value = SubscriptionElementKeep(value).name if value is not None else None
        update(**{'temp': enum_value})
