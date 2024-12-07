# MIGRATIONS/VERSIONS/2404C8BBDA19_ADD_MEDIA_ASSET_TABLE.PY
"""Add media asset table

Revision ID: 2404c8bbda19
Revises: e35d8399bdcf
Create Date: 2023-05-14 12:09:18.044667

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import get_bind


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '2404c8bbda19'
down_revision = 'e35d8399bdcf'
branch_labels = None
depends_on = None

INSERT_UPGRADE_MEDIA_ASSET_LOCATION_TABLE = """
INSERT INTO media_asset_location VALUES
(0, 'primary'),
(1, 'alternate'),
(2, 'archive'),
(3, 'cache'),
(127, 'unknown')
"""

INSERT_POST_INTO_MEDIA_ASSET_TABLE = """
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT post.md5, post.width, post.height, post.size, post.pixel_md5, post.duration, post.audio, post.file_ext, post.alternate AS location_id
FROM POST
"""

INSERT_ARCHIVE_INTO_MEDIA_ASSET_TABLE = """
WITH archive_unwrap AS (
	SELECT unhex("key") AS md5, json_extract(archive.data, '$.body.width') AS width, json_extract(archive.data, '$.body.height') AS height, json_extract(archive.data, '$.body.size') AS size,
		unhex(json_extract(archive.data, '$.body.pixel_md5')) AS pixel_md5, json_extract(archive.data, '$.body.duration') AS duration, json_extract(archive.data, '$.body.audio') AS audio,
		json_extract(archive.data, '$.body.file_ext') AS file_ext, 2 as location_id
	FROM archive
	JOIN archive_type on archive.type_id = archive_type.id
	WHERE archive_type.name = 'post'
)
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT DISTINCT(archive_unwrap.md5), archive_unwrap.width, archive_unwrap.height, archive_unwrap.size, archive_unwrap.pixel_md5, archive_unwrap.duration, archive_unwrap.audio, archive_unwrap.file_ext, archive_unwrap.location_id
FROM archive_unwrap
WHERE archive_unwrap.md5 NOT IN (SELECT media_asset.md5 FROM media_asset)
"""

INSERT_MEDIA_FILE_INTO_MEDIA_ASSET_TABLE = """
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT DISTINCT(media_file.md5), NULL AS width, NULL AS width, NULL AS height, NULL AS size, NULL AS pixel_md5, NULL AS duration, media_file.file_ext, 3 AS location_id
FROM media_file
WHERE md5 not in (SELECT media_asset.md5 FROM media_asset)
"""

INSERT_UPLOAD_ELEMENT_INTO_MEDIA_ASSET_TABLE = """
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT DISTINCT(upload_element.md5), NULL AS width, NULL AS height, NULL AS size, NULL AS pixel_md5, NULL AS duration, NULL AS audio, NULL AS file_ext, NULL AS location_id
FROM upload_element
WHERE upload_element.md5 IS NOT NULL AND upload_element.md5 NOT IN (SELECT media_asset.md5 FROM media_asset)
"""

INSERT_SUBSCRIPTION_ELEMENT_INTO_MEDIA_ASSET_TABLE = """
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT DISTINCT(subscription_element.md5), NULL AS width, NULL AS height, NULL AS size, NULL AS pixel_md5, NULL AS duration, NULL AS audio, NULL AS file_ext, NULL AS location_id
FROM subscription_element
WHERE subscription_element.md5 IS NOT NULL AND subscription_element.md5 NOT IN (SELECT media_asset.md5 FROM media_asset)
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Creating tables")
    op.create_table('media_asset_location',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_media_asset_location')),
    )
    op.create_table('media_asset',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('md5', sa.BLOB(), nullable=False, unique=True),
        sa.Column('width', sa.INTEGER(), nullable=True),
        sa.Column('height', sa.INTEGER(), nullable=True),
        sa.Column('size', sa.INTEGER(), nullable=True),
        sa.Column('pixel_md5', sa.BLOB, nullable=True),
        sa.Column('duration', sa.REAL(), nullable=True),
        sa.Column('audio', sa.BOOLEAN(), nullable=True),
        sa.Column('file_ext', sa.TEXT(), nullable=True),
        sa.Column('location_id', sa.INTEGER(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_media_asset')),
        sa.ForeignKeyConstraint(['location_id'], ['media_asset_location.id'], ),
    )

    #print("Creating index")
    #with op.batch_alter_table('media_asset', schema=None) as batch_op:
    #    batch_op.create_index(batch_op.f('ix_media_asset_md5'), ['md5'], unique=True)

    print("Populating tables")
    conn = get_bind()
    conn.execute(sa.text(INSERT_UPGRADE_MEDIA_ASSET_LOCATION_TABLE.strip()))
    print("Inserting posts")
    conn.execute(sa.text(INSERT_POST_INTO_MEDIA_ASSET_TABLE.strip()))
    print("Inserting archives")
    conn.execute(sa.text(INSERT_ARCHIVE_INTO_MEDIA_ASSET_TABLE.strip()))
    print("Inserting media_files")
    conn.execute(sa.text(INSERT_MEDIA_FILE_INTO_MEDIA_ASSET_TABLE.strip()))
    print("Inserting upload_elements")
    conn.execute(sa.text(INSERT_UPLOAD_ELEMENT_INTO_MEDIA_ASSET_TABLE.strip()))
    print("Inserting subscription_elements")
    conn.execute(sa.text(INSERT_SUBSCRIPTION_ELEMENT_INTO_MEDIA_ASSET_TABLE.strip()))

def downgrade_():
    #with op.batch_alter_table('media_asset', schema=None) as batch_op:
    #    batch_op.drop_index(batch_op.f('ix_media_asset_md5'))

    op.drop_table('media_asset')
    op.drop_table('media_asset_location')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
