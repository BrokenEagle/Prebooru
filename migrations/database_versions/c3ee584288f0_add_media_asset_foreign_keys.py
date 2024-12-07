# MIGRATIONS/VERSIONS/C3EE584288F0_ADD_MEDIA_ASSET_FOREIGN_KEYS.PY
"""Add media asset foreign keys

Revision ID: c3ee584288f0
Revises: 2404c8bbda19
Create Date: 2023-05-14 12:26:26.953581

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import alter_column, add_column, drop_column
from migrations.constraints import add_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'c3ee584288f0'
down_revision = '2404c8bbda19'
branch_labels = None
depends_on = None


UPDATE_MEDIA_ASSET_ID = """
UPDATE {0}
SET media_asset_id = (
    SELECT media_asset.id FROM media_asset WHERE {0}.md5 = media_asset.md5
)"""

UPDATE_ARCHIVE_MEDIA_ASSET_ID = """
UPDATE archive
SET media_asset_id = media_asset.id
FROM media_asset
WHERE media_asset.md5 = unhex(archive."key")
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Adding columns")
    with op.batch_alter_table('post', schema=None) as batch_op:
        add_column(None, 'media_asset_id', 'INTEGER', batch_op=batch_op)
        alter_column(None, 'media_asset_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_post_media_asset_id_media_asset', 'foreignkey', ('media_asset', ['media_asset_id'], ['id']), batch_op=batch_op)

    with op.batch_alter_table('archive', schema=None) as batch_op:
        add_column(None, 'media_asset_id', 'INTEGER', batch_op=batch_op)
        alter_column(None, 'media_asset_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_archive_media_asset_id_media_asset', 'foreignkey', ('media_asset', ['media_asset_id'], ['id']), batch_op=batch_op)

    with op.batch_alter_table('media_file', schema=None) as batch_op:
        add_column(None, 'media_asset_id', 'INTEGER', batch_op=batch_op)
        alter_column(None, 'media_asset_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_media_file_media_asset_id_media_asset', 'foreignkey', ('media_asset', ['media_asset_id'], ['id']), batch_op=batch_op)

    with op.batch_alter_table('upload_element', schema=None) as batch_op:
        add_column(None, 'media_asset_id', 'INTEGER', batch_op=batch_op)
        alter_column(None, 'media_asset_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_upload_element_media_asset_id_media_asset', 'foreignkey', ('media_asset', ['media_asset_id'], ['id']), batch_op=batch_op)

    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        add_column(None, 'media_asset_id', 'INTEGER', batch_op=batch_op)
        alter_column(None, 'media_asset_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_subscription_element_media_asset_id_media_asset', 'foreignkey', ('media_asset', ['media_asset_id'], ['id']), batch_op=batch_op)

    print("Populating columns")
    conn = op.get_bind()
    conn.execute(sa.text(UPDATE_MEDIA_ASSET_ID.format('post')))
    conn.execute(sa.text(UPDATE_ARCHIVE_MEDIA_ASSET_ID))
    conn.execute(sa.text(UPDATE_MEDIA_ASSET_ID.format('media_file')))
    conn.execute(sa.text(UPDATE_MEDIA_ASSET_ID.format('upload_element')))
    conn.execute(sa.text(UPDATE_MEDIA_ASSET_ID.format('subscription_element')))

    print("Alter columns nullable")
    alter_column('post', 'media_asset_id', 'INTEGER', {'nullable': False})
    alter_column('media_file', 'media_asset_id', 'INTEGER', {'nullable': False})


def downgrade_():
    remove_temp_tables(['upload_element', 'subscription_element', 'post', 'archive', 'media_file'])

    with op.batch_alter_table('subscription_element', schema=None) as batch_op:
        drop_constraint(None, 'fk_subscription_element_media_asset_id_media_asset', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'media_asset_id', batch_op=batch_op)

    with op.batch_alter_table('upload_element', schema=None) as batch_op:
        drop_constraint(None, 'fk_upload_element_media_asset_id_media_asset', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'media_asset_id', batch_op=batch_op)

    with op.batch_alter_table('media_file', schema=None) as batch_op:
        drop_constraint(None, 'fk_media_file_media_asset_id_media_asset', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'media_asset_id', batch_op=batch_op)

    with op.batch_alter_table('archive', schema=None) as batch_op:
        drop_constraint(None, 'fk_archive_media_asset_id_media_asset', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'media_asset_id', batch_op=batch_op)

    with op.batch_alter_table('post', schema=None) as batch_op:
        drop_constraint(None, 'fk_post_media_asset_id_media_asset', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'media_asset_id', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
