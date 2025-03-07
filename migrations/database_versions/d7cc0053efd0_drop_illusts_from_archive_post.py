# MIGRATIONS/VERSIONS/D7CC0053EFD0_DROP_ILLUSTS_FROM_ARCHIVE_POST.PY
"""Drop illusts from archive_post

Revision ID: d7cc0053efd0
Revises: 42c4f1a4b54f
Create Date: 2025-03-06 12:00:52.902716

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd7cc0053efd0'
down_revision = '42c4f1a4b54f'
branch_labels = None
depends_on = None

ARCHIVE_POST_ILLUSTS_DOWNGRADE = """
WITH
illust_urls AS (
	SELECT
		single_url.md5,
		json_group_array(single_url.url) AS illusts
	FROM (
		SELECT
			CASE site_descriptor.name
				WHEN 'twimg' THEN concat('https://pbs.twimg.com', illust_url.url)
				WHEN 'twvideo' THEN concat('https://video.twimg.com', illust_url.url)
				WHEN 'twvideo_cf' THEN concat('https://video-cf.twimg.com', illust_url.url)
				WHEN 'pximg' THEN concat('https://i.pximg.net', illust_url.url)
				ELSE illust_url.url
			END AS url,
			illust_url.md5
		FROM illust_url
		JOIN site_descriptor ON site_descriptor.id = illust_url.site_id
		UNION
		SELECT 
			json_extract(illusts.value, '$[1]') AS url,
			unhex(json_extract(illusts.value, '$[6]')) AS md5
		FROM archive_illust
		JOIN json_each(archive_illust.urls, '$') AS illusts
	) AS single_url
	GROUP BY single_url.md5
)
UPDATE archive_post
SET illusts = illust_urls.illusts
FROM illust_urls WHERE illust_urls.md5 = archive_post.md5
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_column('archive_post', 'illusts')


def downgrade_():
    connection = op.get_bind()

    print("Adding illusts column")
    add_column('archive_post', 'illusts', 'JSON')

    print("Populating post_id column")
    connection.execute(ARCHIVE_POST_ILLUSTS_DOWNGRADE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

