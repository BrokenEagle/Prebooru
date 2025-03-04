# MIGRATIONS/VERSIONS/A57030B7F31A_ADD_MD5_TO_ILLUST_URL.PY
"""Add md5 to illust_url

Revision ID: a57030b7f31a
Revises: daa9250f64f8
Create Date: 2025-03-03 10:44:36.468372

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index, make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'a57030b7f31a'
down_revision = 'daa9250f64f8'
branch_labels = None
depends_on = None

ILLUST_URL_MD5_UPGRADE = """
WITH
all_md5s AS (
	SELECT
		illust_url.id,
		COALESCE(post.md5, download_element.md5, subscription_element.md5) AS md5
	FROM illust_url
	LEFT JOIN post ON post.id = illust_url.post_id
	LEFT JOIN download_element ON download_element.illust_url_id = illust_url.id
	LEFT JOIN subscription_element ON subscription_element.illust_url_id = illust_url.id
	GROUP BY illust_url.id
)
UPDATE illust_url
SET md5 = all_md5s.md5
FROM all_md5s
WHERE all_md5s.id = illust_url.id
"""

RESTORE_INDEX = make_index_wrapper('illust_url', [
    ('ix_illust_url_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    connection = op.get_bind()

    print("Adding md5 column")
    add_column('illust_url', 'md5', 'BLOB')

    print("Populating md5 column")
    connection.execute(ILLUST_URL_MD5_UPGRADE)

    print("Creating md5 index")
    create_index('illust_url', 'ix_illust_url_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')


@RESTORE_INDEX
def downgrade_():
    drop_index('illust_url', 'ix_illust_url_md5')
    drop_column('illust_url', 'md5')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
