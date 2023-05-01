# MIGRATIONS/VERSIONS/B55524FC260B_REMOVE_MEDIA_INFO_FROM_APPLICABLE_RECORDS.PY
"""Remove media info from applicable records

Revision ID: b55524fc260b
Revises: c3ee584288f0
Create Date: 2023-05-23 05:46:43.570092

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import get_bind
from migrations.columns import add_columns, add_column, alter_columns, drop_columns, drop_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'b55524fc260b'
down_revision = 'c3ee584288f0'
branch_labels = None
depends_on = None

INSERT_DOWNGRADE_POST_TABLE = """
REPLACE INTO post(id, danbooru_id, simcheck, created, media_asset_id, type_id, md5, height, width, size, file_ext, pixel_md5, audio, duration, alternate)
SELECT post.id, post.danbooru_id, post.simcheck, post.created, post.media_asset_id, post.type_id,
       media_asset.md5, media_asset.height, media_asset.width, media_asset.size, media_asset.file_ext,
       media_asset.pixel_md5, media_asset.audio, media_asset.duration, iif(media_asset_location.name = 'alternate', 1, 0) AS alternate
FROM post
INNER JOIN media_asset ON post.media_asset_id = media_asset.id
INNER JOIN media_asset_location on media_asset.location_id = media_asset_location.id
"""

INSERT_DOWNGRADE_MEDIA_FILE_TABLE = """
REPLACE INTO media_file(id, media_url, expires, media_asset_id, md5, file_ext)
SELECT media_file.id, media_file.media_url, media_file.expires, media_file.media_asset_id,
       media_asset.md5, media_asset.file_ext
FROM media_file
INNER JOIN media_asset ON media_file.media_asset_id = media_asset.id
"""

INSERT_DOWNGRADE_SUBSCRIPTION_ELEMENT_TABLE = """
REPLACE INTO subscription_element(id, subscription_id, post_id, illust_url_id, status_id, keep_id, expires, media_asset_id, md5)
SELECT subscription_element.id, subscription_element.subscription_id, subscription_element.post_id, subscription_element.illust_url_id,
       subscription_element.status_id, subscription_element.keep_id, subscription_element.expires, subscription_element.media_asset_id,
       media_asset.md5
FROM subscription_element
INNER JOIN media_asset on subscription_element.media_asset_id = media_asset.id
"""

INSERT_DOWNGRADE_UPLOAD_ELEMENT_TABLE = """
REPLACE INTO upload_element(id, upload_id, illust_url_id, status_id, media_asset_id, md5)
SELECT upload_element.id, upload_element.upload_id, upload_element.illust_url_id, upload_element.status_id, upload_element.media_asset_id,
       media_asset.md5
FROM upload_element
INNER JOIN media_asset on upload_element.media_asset_id = media_asset.id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Dropping indexes")
    drop_index('post', 'ix_post_md5')
    drop_index('subscription_element', 'ix_subscription_element_md5')
    drop_index('upload_element', 'ix_upload_element_md5')

    print("Dropping columns")
    drop_columns('media_file', ['md5', 'file_ext'])
    drop_columns('post', ['md5', 'height', 'width', 'size', 'file_ext', 'alternate', 'pixel_md5', 'audio', 'duration'])
    drop_column('subscription_element', 'md5')
    drop_column('upload_element', 'md5')


def downgrade_():
    print("Adding columns")
    add_column('upload_element', 'md5', 'BLOB')
    add_column('subscription_element', 'md5', 'BLOB')
    add_columns('post', [
        ('height', 'INTEGER'),
        ('width', 'INTEGER'),
        ('size', 'INTEGER'),
        ('md5', 'BLOB'),
        ('file_ext', 'TEXT'),
        ('pixel_md5', 'BLOB'),
        ('audio', 'BOOLEAN'),
        ('duration', 'FLOAT'),
        ('alternate', 'BOOLEAN'),
    ])
    add_columns('media_file', [
        ('md5', 'BLOB'),
        ('file_ext', 'TEXT'),
    ])

    print("Populating tables")
    conn = get_bind()
    conn.execute(sa.text(INSERT_DOWNGRADE_POST_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_MEDIA_FILE_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_SUBSCRIPTION_ELEMENT_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_UPLOAD_ELEMENT_TABLE.strip()))

    print("Updating nullable constraint")
    alter_columns('post', [
        ('height', 'INTEGER', {'nullable': False}),
        ('width', 'INTEGER', {'nullable': False}),
        ('size', 'INTEGER', {'nullable': False}),
        ('md5', 'BLOB', {'nullable': False}),
        ('file_ext', 'TEXT', {'nullable': False}),
        ('alternate', 'BOOLEAN', {'nullable': False}),
    ])
    alter_columns('media_file', [
        ('md5', 'BLOB', {'nullable': False}),
        ('file_ext', 'TEXT', {'nullable': False}),
    ])


    print("Creating indexes")
    create_index('post', 'ix_post_md5', ['md5'], True)
    create_index('subscription_element', 'ix_subscription_element_md5', ['md5'], False)
    create_index('upload_element', 'ix_upload_element_md5', ['md5'], False)

def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
