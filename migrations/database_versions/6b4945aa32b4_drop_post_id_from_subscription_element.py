# MIGRATIONS/VERSIONS/6B4945AA32B4_DROP_POST_ID_FROM_SUBSCRIPTION_ELEMENT.PY
"""Drop post_id from subscription_element

Revision ID: 6b4945aa32b4
Revises: d7cc0053efd0
Create Date: 2025-03-10 11:24:56.187493

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '6b4945aa32b4'
down_revision = 'd7cc0053efd0'
branch_labels = None
depends_on = None

SUBSCRIPTION_ELEMENT_POST_ID_DOWNGRADE = """
WITH
subscription_element_post_id AS (
	SELECT
		subscription_element.id,
		post.id AS post_id
	FROM subscription_element
	JOIN illust_url ON illust_url.id = subscription_element.illust_url_id
	JOIN post ON post.md5 = illust_url.md5
	JOIN subscription_element_status ON subscription_element_status.id = subscription_element.status_id
	WHERE subscription_element_status.name = 'active'
)
UPDATE subscription_element
SET post_id = subscription_element_post_id.post_id
FROM subscription_element_post_id
WHERE subscription_element.id = subscription_element_post_id.id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_index('subscription_element', 'ix_subscription_element_post_id')
    drop_column('subscription_element', 'post_id')
    create_index('subscription_element', 'ix_subscription_element_illust_url_id', ['illust_url_id'], True)


def downgrade_():
    connection = op.get_bind()

    print("Dropping illust_url_id index")
    drop_index('subscription_element', 'ix_subscription_element_illust_url_id')

    print("Adding post_id column")
    add_column('subscription_element', 'post_id', 'INTEGER')

    print("Populating post_id column")
    connection.execute(SUBSCRIPTION_ELEMENT_POST_ID_DOWNGRADE)

    print("Creating post_id index")
    create_index('subscription_element', 'ix_subscription_element_post_id', ['post_id'], False, sqlite_where='post_id IS NOT NULL')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

