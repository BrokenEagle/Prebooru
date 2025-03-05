# MIGRATIONS/VERSIONS/30C1648E03EB_DROP_MD5_FROM_SUBSCRIPTION_ELEMENT.PY
"""Drop md5 from subscription element

Revision ID: 30c1648e03eb
Revises: 56290c546fd0
Create Date: 2025-03-05 15:17:34.728396

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index, make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '30c1648e03eb'
down_revision = '56290c546fd0'
branch_labels = None
depends_on = None

SUBSCRIPTION_ELEMENT_MD5_DOWNGRADE = """
WITH
illust_url_md5 AS (
	SELECT
		illust_url.id,
		illust_url.md5
	FROM illust_url
)
UPDATE subscription_element
SET md5 = illust_url_md5.md5
FROM illust_url_md5
WHERE subscription_element.illust_url_id = illust_url_md5.id
"""

RESTORE_INDEX = make_index_wrapper('subscription_element', [
    ('ix_subscription_element_post_id', ['post_id'], True, {'sqlite_where': 'post_id IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    drop_index('subscription_element', 'ix_subscription_element_md5')
    drop_column('subscription_element', 'md5')


@RESTORE_INDEX
def downgrade_():
    connection = op.get_bind()

    print("Adding md5 column")
    add_column('subscription_element', 'md5', 'BLOB')

    print("Populating md5 column")
    connection.execute(SUBSCRIPTION_ELEMENT_MD5_DOWNGRADE)

    print("Creating md5 index")
    create_index('subscription_element', 'ix_subscription_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

