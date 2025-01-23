# MIGRATIONS/VERSIONS/A83C28EE0A01_SPLIT_UPLOAD_TABLE_INTO_UPLOADS_DOWNLOADS.PY
"""Split upload table into uploads/downloads

Revision ID: a83c28ee0a01
Revises: 20ef223031ad
Create Date: 2024-12-18 20:07:21.019591

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table
from migrations.columns import add_columns, drop_columns
from migrations.constraints import create_constraints, drop_constraints, create_constraint
from migrations.indexes import create_index, create_indexes, drop_indexes

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'a83c28ee0a01'
down_revision = '20ef223031ad'
branch_labels = None
depends_on = None

DOWNLOAD_STATUS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_download_status',
            'columns': ['id'],
        },
    ],
    'with_rowid': True,
}

DOWNLOAD_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'request_url',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'status_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'created',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_download',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_download_status_id_download_status',
            'columns': ['status_id'],
            'references': ['download_status.id'],
        },
    ],
    'with_rowid': True,
}

DOWNLOAD_ELEMENT_STATUS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_download_element_status',
            'columns': ['id'],
        },
    ],
    'with_rowid': True,
}

DOWNLOAD_ELEMENT_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'download_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'illust_url_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'status_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'md5',
            'type': 'BLOB',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_download_element',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_download_element_download_id_download',
            'columns': ['download_id'],
            'references': ['download.id'],
        }, {
            'name': 'fk_download_element_illust_url_id_illust_url',
            'columns': ['illust_url_id'],
            'references': ['illust_url.id'],
        }, {
            'name': 'fk_download_element_status_id_upload_element_status',
            'columns': ['status_id'],
            'references': ['download_element_status.id'],
        },
    ],
    'with_rowid': True,
}

DOWNLOAD_URL_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'url',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'download_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_download_url',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_download_url_download_id_download',
            'columns': ['download_id'],
            'references': ['download.id'],
        },
    ],
    'with_rowid': True,
}

DOWNLOAD_STATUS_INSERT = """
INSERT INTO download_status (id, name)
SELECT upload_status.id, upload_status.name
FROM upload_status
"""

DOWNLOAD_INSERT = """
INSERT INTO download (id, request_url, status_id, created)
SELECT upload.id, upload.request_url, upload.status_id, upload.created
FROM upload
WHERE upload.request_url IS NOT NULL
"""

DOWNLOAD_ELEMENT_STATUS_INSERT = """
INSERT INTO download_element_status (id, name)
SELECT upload_element_status.id, upload_element_status.name
FROM upload_element_status
"""

DOWNLOAD_ELEMENT_INSERT = """
INSERT INTO download_element (id, download_id, illust_url_id, status_id, md5)
SELECT upload_element.id, upload_element.upload_id, upload_element.illust_url_id, upload_element.status_id, upload_element.md5
FROM upload_element
JOIN upload ON upload.id = upload_element.upload_id
WHERE upload.request_url IS NOT NULL
"""

DOWNLOAD_URL_INSERT = """
INSERT INTO download_url (id, url, download_id)
SELECT upload_url.id, upload_url.url, upload_url.upload_id
FROM upload_url
JOIN upload ON upload.id = upload_url.upload_id
WHERE upload.request_url IS NOT NULL
"""

ERROR_TABLE_DOWNLOAD_UPGRADE = """
REPLACE INTO error (id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id, download_id, download_element_id)
SELECT error.id, error.module, error.message, error.created, NULL, NULL, NULL, NULL, NULL, error.upload_id, NULL
FROM error
JOIN upload ON upload.id = error.upload_id
WHERE upload.request_url IS NOT NULL
"""

ERROR_TABLE_DOWNLOAD_ELEMENT_UPGRADE = """
REPLACE INTO error (id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id, download_id, download_element_id)
SELECT error.id, error.module, error.message, error.created, NULL, NULL, NULL, NULL, NULL, NULL, error.upload_element_id
FROM error
WHERE error.upload_element_id IS NOT NULL
"""

ERROR_TABLE_UPLOAD_DOWNGRADE = """
REPLACE INTO error (id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id, download_id, download_element_id)
SELECT error.id, error.module, error.message, error.created, NULL, NULL, NULL, error.download_id, NULL, NULL, NULL
FROM error
JOIN download ON download.id = error.download_id
WHERE download.request_url IS NOT NULL
"""

ERROR_TABLE_UPLOAD_ELEMENT_DOWNGRADE = """
REPLACE INTO error (id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id, download_id, download_element_id)
SELECT error.id, error.module, error.message, error.created, NULL, NULL, NULL, NULL, error.download_element_id, NULL, NULL
FROM error
WHERE error.download_element_id IS NOT NULL
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating download status table")
    create_table('download_status', **DOWNLOAD_STATUS_TABLE_CONFIG)
    connection.execute(DOWNLOAD_STATUS_INSERT)

    print("Creating download table")
    create_table('download', **DOWNLOAD_TABLE_CONFIG)
    connection.execute(DOWNLOAD_INSERT)

    print("Creating download element status table")
    create_table('download_element_status', **DOWNLOAD_ELEMENT_STATUS_TABLE_CONFIG)
    connection.execute(DOWNLOAD_ELEMENT_STATUS_INSERT)

    print("Creating download element table")
    create_table('download_element', **DOWNLOAD_ELEMENT_TABLE_CONFIG)
    connection.execute(DOWNLOAD_ELEMENT_INSERT)
    create_indexes('download_element', [
        ('ix_download_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
        ('ix_download_element_download_id', ['download_id'], False),
    ])

    print("Creating download url table")
    create_table('download_url', **DOWNLOAD_URL_TABLE_CONFIG)
    connection.execute(DOWNLOAD_URL_INSERT)
    create_index('download_url', 'ix_download_url_download_id', ['download_id'], False)

    print("Adding download foreign keys to error table")
    add_columns('error', [('download_id', 'INTEGER'), ('download_element_id', 'INTEGER')])
    create_constraints('error', [
        ('fk_error_download_id_download', 'foreignkey', ('download', ['download_id'], ['id'])),
        ('fk_error_download_element_id_download_element', 'foreignkey', ('download_element', ['download_element_id'], ['id'])),
    ])
    connection.execute(ERROR_TABLE_DOWNLOAD_UPGRADE)
    connection.execute(ERROR_TABLE_DOWNLOAD_ELEMENT_UPGRADE)
    # The check constraint is removed already, and trying to remove it before adding the columns causes an exception since the constraint can't be found
    create_constraint('error', 'ck_error_attachments', 'check', ["((post_id IS NULL) + (subscription_id IS NULL) + (subscription_element_id IS NULL) + (upload_id IS NULL) + (upload_element_id IS NULL) + (download_id IS NULL) + (download_element_id IS NULL)) in (6, 7)"])
    create_indexes('error', [
        ('ix_error_download_id', ['download_id'], False, {'sqlite_where': 'download_id IS NOT NULL'}),
        ('ix_error_download_element_id', ['download_element_id'], False, {'sqlite_where': 'download_element_id IS NOT NULL'}),
    ])
    _restore_error_table_indexes()

def downgrade_():
    connection = op.get_bind()

    print("Removing download foreign keys from error table")
    drop_indexes('error', ['ix_error_download_id', 'ix_error_download_element_id'])
    drop_constraints('error', [
        ('ck_error_attachments', 'check'),
        ('fk_error_download_id_download', 'foreignkey'),
        ('fk_error_download_element_id_download_element', 'foreignkey'),
    ])
    connection.execute(ERROR_TABLE_UPLOAD_DOWNGRADE)
    connection.execute(ERROR_TABLE_UPLOAD_ELEMENT_DOWNGRADE)
    drop_columns('error', ['download_id', 'download_element_id'])
    create_constraint('error', 'ck_error_attachments', 'check', ["((post_id IS NULL) + (subscription_id IS NULL) + (subscription_element_id IS NULL) + (upload_id IS NULL) + (upload_element_id IS NULL)) in (4, 5)"])
    _restore_error_table_indexes()

    print("Dropping tables")
    drop_table('download_url')
    drop_table('download_element')
    drop_table('download_element_status')
    drop_table('download')
    drop_table('download_status')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass


# ## PRIVATE

def _restore_error_table_indexes():
    """Alembic isn't able to properly restore partial indexes, so do it manually"""
    drop_indexes('error', ['ix_error_post_id', 'ix_error_upload_id', 'ix_error_upload_element_id', 'ix_error_subscription_id', 'ix_error_subscription_element_id'])
    create_indexes('error', [
        ('ix_error_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ('ix_error_upload_id', ['upload_id'], False, {'sqlite_where': 'upload_id IS NOT NULL'}),
        ('ix_error_upload_element_id', ['upload_element_id'], False, {'sqlite_where': 'upload_element_id IS NOT NULL'}),
        ('ix_error_subscription_id', ['subscription_id'], False, {'sqlite_where': 'subscription_id IS NOT NULL'}),
        ('ix_error_subscription_element_id', ['subscription_element_id'], False, {'sqlite_where': 'subscription_element_id IS NOT NULL'}),
    ])
