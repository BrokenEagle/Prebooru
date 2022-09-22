"""Change subscription element status to enum

Revision ID: a4059b46e578
Revises: ce08edf27b4d
Create Date: 2022-09-22 10:23:28.867677

"""

# ## PYTHON IMPORTS
import re

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'a4059b46e578'
down_revision = 'ce08edf27b4d'
branch_labels = None
depends_on = None

TYPE_RG = None


# ## FUNCTIONS

def init():
    global SubscriptionElementStatus, TYPE_RG
    from app.models.subscription_element import SubscriptionElementStatus
    TYPE_RG = re.compile('|'.join(SubscriptionElementStatus.names))


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()
    t_subscription_element = sa.Table(
        'subscription_element',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('status', sa.String),
        sa.Column('temp', sa.Integer),
    )

    print("Adding temp column")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.Integer(), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        element_data = connection.execute(sa.select([t_subscription_element.c.id, t_subscription_element.c.status]).limit(1000).offset(index * 1000)).fetchall()
        for element in element_data:
            try:
                enum_name = TYPE_RG.match(element[1]).group(0)
            except Exception as e:
                print(element, TYPE_RG)
                raise e
            enum_value = SubscriptionElementStatus[enum_name].value
            connection.execute(t_subscription_element.update().where(t_subscription_element.c.id == element[0]).values(
                temp=enum_value,
                ))
        if len(element_data):
            print(f"subscription element #{element_data[0][0]} - subscription element #{element_data[-1][0]}")
        if len(element_data) < 1000:
            break
        index += 1

    print("Dropping status column")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.drop_column('status')

    print("Renaming temp column to status")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='status',
                              existing_type=sa.INTEGER(),
                              nullable=False
                              )

    # ### end Alembic commands ###


def downgrade_():
    print("Initializing")
    init()
    t_subscription_element = sa.Table(
        'subscription_element',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('status', sa.Integer),
        sa.Column('temp', sa.String),
    )

    print("Adding temp column")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.VARCHAR(length=16), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        post_data = connection.execute(sa.select([t_subscription_element.c.id, t_subscription_element.c.status]).limit(1000).offset(index * 1000)).fetchall()
        for subscription_element in post_data:
            connection.execute(t_subscription_element.update().where(t_subscription_element.c.id == subscription_element[0]).values(
                temp=SubscriptionElementStatus(subscription_element[1]).name,
                ))
        if len(post_data):
            print(f"subscription element #{post_data[0][0]} - subscription element #{post_data[-1][0]}")
        if len(post_data) < 1000:
            break
        index += 1

    print("Dropping old status column")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.drop_column('status')

    print("Renaming temp column to status")
    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='status',
                              existing_type=sa.VARCHAR(),
                              nullable=False
                              )

