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

INSERT_UPGRADE_MEDIA_ASSET_TABLE = """
WITH all_md5s AS (
	SELECT post.md5, post.width, post.height, post.size, post.pixel_md5, post.duration, post.audio, post.file_ext
	FROM post
	UNION ALL
	SELECT media_file.md5, NULL, NULL, NULL, NULL, NULL, NULL, media_file.file_ext
	FROM media_file
	UNION ALL
	SELECT upload_element.md5, NULL, NULL, NULL, NULL, NULL, NULL, NULL
	FROM upload_element
	WHERE upload_element.md5 IS NOT NULL
	UNION ALL
	SELECT subscription_element.md5, NULL, NULL, NULL, NULL, NULL, NULL, NULL
	FROM subscription_element
	WHERE subscription_element.md5 IS NOT NULL
)
INSERT INTO media_asset(md5, width, height, size, pixel_md5, duration, audio, file_ext)
SELECT ordered_md5s.md5, ordered_md5s.width, ordered_md5s.height, ordered_md5s.size, ordered_md5s.pixel_md5, ordered_md5s.duration, ordered_md5s.audio, ordered_md5s.file_ext
FROM (
	SELECT *, row_number() OVER (
		PARTITION BY all_md5s.md5
		ORDER BY
		CASE
			WHEN file_ext IS NULL THEN 2 
			WHEN size IS NULL THEN 1
			ELSE 0
		END
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
    print("Creating table")
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
        sa.PrimaryKeyConstraint('id', name=op.f('pk_media_asset'))
    )

    print("Creating index")
    with op.batch_alter_table('media_asset', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_media_asset_md5'), ['md5'], unique=True)

    print("Populating table")
    conn = get_bind()
    conn.execute(sa.text(INSERT_UPGRADE_MEDIA_ASSET_TABLE.strip()))


def downgrade_():
    with op.batch_alter_table('media_asset', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_media_asset_md5'))

    op.drop_table('media_asset')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
