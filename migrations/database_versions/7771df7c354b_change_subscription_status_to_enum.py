# MIGRATIONS/VERSIONS/7771DF7C354B_CHANGE_SUBSCRIPTION_STATUS_TO_ENUM.PY
"""Change Subscription status to enum

Revision ID: 7771df7c354b
Revises: 7afcb396fbd8
Create Date: 2022-09-29 11:11:57.466449

"""

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, transfer_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7771df7c354b'
down_revision = '7afcb396fbd8'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def init():
    global SubscriptionStatus
    from app.models.subscription import SubscriptionStatus


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('subscription', 'temp', 'Integer')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('subscription', ('status', 'String'), ('temp', 'Integer')):
        enum_value = SubscriptionStatus[value].value
        update(**{'temp': enum_value})

    print("Dropping status column")
    drop_column('subscription', 'status')

    print("Renaming temp column to status")
    alter_column('subscription', 'temp', 'INTEGER', {'new_column_name': 'status', 'nullable': False})


def downgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('subscription', 'temp', 'String')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('subscription', ('status', 'Integer'), ('temp', 'String')):
        enum_name = SubscriptionStatus(value).name
        update(**{'temp': enum_name})

    print("Dropping status column")
    drop_column('subscription', 'status')

    print("Renaming temp column to status")
    alter_column('subscription', 'temp', 'VARCHAR', {'new_column_name': 'status', 'nullable': False})
