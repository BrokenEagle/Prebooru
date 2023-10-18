# MIGRATIONS/VERSIONS/2404C8BBDA19_ADD_MEDIA_ASSET_TABLE.PY
"""Add media asset table

Revision ID: 2404c8bbda19
Revises: 7262282fa74a
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
down_revision = '7262282fa74a'
branch_labels = None
depends_on = None

INSERT_UPGRADE_MEDIA_ASSET_LOCATION_TABLE = """
INSERT INTO media_asset_location VALUES
(0, 'primary'),
(1, 'alternate'),
(2, 'archive'),
(3, 'cache'),
(127, 'unknown'),
"""

INSERT_UPGRADE_MEDIA_ASSET_TABLE = """
WITH all_md5s AS (
	SELECT post.md5, post.width, post.height, post.size, post.pixel_md5, post.duration, post.audio, post.file_ext, post.alternate AS location_id
	FROM post
	UNION ALL
	SELECT unhex("key") AS md5, json_extract(archive.data, '$.body.width') AS width, json_extract(archive.data, '$.body.height') AS height, json_extract(archive.data, '$.body.size') AS size,
		unhex(json_extract(archive.data, '$.body.pixel_md5')) AS pixel_md5, json_extract(archive.data, '$.body.duration') AS duration, json_extract(archive.data, '$.body.audio') AS audio,
		json_extract(archive.data, '$.body.file_ext') AS file_ext, 2
	FROM archive
	INNER JOIN archive_type ON archive.type_id = archive_type.id
	WHERE archive_type.name = 'post'
	UNION ALL
	SELECT media_file.md5, NULL, NULL, NULL, NULL, NULL, NULL, media_file.file_ext, 3
	FROM media_file
	UNION ALL
	SELECT upload_element.md5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
	FROM upload_element
	WHERE upload_element.md5 IS NOT NULL
	UNION ALL
	SELECT subscription_element.md5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
	FROM subscription_element
	WHERE subscription_element.md5 IS NOT NULL
)
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext, location_id)
SELECT ordered_md5s.md5, ordered_md5s.width, ordered_md5s.height, ordered_md5s.size, ordered_md5s.pixel_md5, ordered_md5s.duration, ordered_md5s.audio, ordered_md5s.file_ext, ordered_md5s.location_id
FROM (
	SELECT *, row_number() OVER (
		PARTITION BY all_md5s.md5
		ORDER BY all_md5s.location_id ASC NULLS LAST
	) AS rn
	FROM all_md5s
) AS ordered_md5s
WHERE ordered_md5s.rn = 1
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
        sa.Column('md5', sa.BLOB(), nullable=False),
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

    print("Populating tables")
    conn = get_bind()
    conn.execute(sa.text(INSERT_UPGRADE_MEDIA_ASSET_LOCATION_TABLE.strip()))
    conn.execute(sa.text(INSERT_UPGRADE_MEDIA_ASSET_TABLE.strip()))

    print("Creating index")
    with op.batch_alter_table('media_asset', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_media_asset_md5'), ['md5'], unique=True)

def downgrade_():
    #with op.batch_alter_table('media_asset', schema=None) as batch_op:
    #    batch_op.drop_index(batch_op.f('ix_media_asset_md5'))

    op.drop_table('media_asset')
    op.drop_table('media_asset_location')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
