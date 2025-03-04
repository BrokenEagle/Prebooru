# MIGRATIONS/VERSIONS/56290C546FD0_DROP_MD5_FROM_DOWNLOAD_ELEMENT.PY
"""Drop md5 from download element

Revision ID: 56290c546fd0
Revises: a57030b7f31a
Create Date: 2025-03-04 09:55:58.362368

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '56290c546fd0'
down_revision = 'a57030b7f31a'
branch_labels = None
depends_on = None

DOWNLOAD_ELEMENT_MD5_DOWNGRADE = """
WITH
illust_url_md5 AS (
	SELECT
		illust_url.id,
		illust_url.md5
	FROM illust_url
)
UPDATE download_element
SET md5 = illust_url_md5.md5
FROM illust_url_md5
WHERE download_element.illust_url_id = illust_url_md5.id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_index('download_element', 'ix_download_element_md5')
    drop_column('download_element', 'md5')


def downgrade_():
    connection = op.get_bind()

    print("Adding md5 column")
    add_column('download_element', 'md5', 'BLOB')

    print("Populating md5 column")
    connection.execute(DOWNLOAD_ELEMENT_MD5_DOWNGRADE)

    print("Creating md5 index")
    create_index('download_element', 'ix_download_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

