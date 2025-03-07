# MIGRATIONS/VERSIONS/42C4F1A4B54F_DROP_POST_ID_FROM_ILLUST_URL.PY
"""Drop post_id from illust_url

Revision ID: 42c4f1a4b54f
Revises: 30c1648e03eb
Create Date: 2025-03-06 09:47:06.573558

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index, make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '42c4f1a4b54f'
down_revision = '30c1648e03eb'
branch_labels = None
depends_on = None

ILLUST_URL_POST_ID_DOWNGRADE = """
WITH
illust_url_post_id AS (
	SELECT
		illust_url.id,
		post.id AS post_id
	FROM illust_url
	JOIN post ON post.md5 = illust_url.md5
)
UPDATE illust_url
SET post_id = illust_url_post_id.post_id
FROM illust_url_post_id
WHERE illust_url.id = illust_url_post_id.id
"""

RESTORE_INDEX = make_index_wrapper('illust_url', [
    ('ix_illust_url_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    drop_index('illust_url', 'ix_illust_url_post_id')
    drop_column('illust_url', 'post_id')


@RESTORE_INDEX
def downgrade_():
    connection = op.get_bind()

    print("Adding post_id column")
    add_column('illust_url', 'post_id', 'INTEGER')

    print("Populating post_id column")
    connection.execute(ILLUST_URL_POST_ID_DOWNGRADE)

    print("Creating post_id index")
    create_index('illust_url', 'ix_illust_url_post_id', ['post_id'], False, sqlite_where='post_id IS NOT NULL')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

