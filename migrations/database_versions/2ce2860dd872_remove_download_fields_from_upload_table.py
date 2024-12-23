# MIGRATIONS/VERSIONS/2CE2860DD872_REMOVE_DOWNLOAD_FIELDS_FROM_UPLOAD_TABLE.PY
"""Remove download fields from upload table

Revision ID: 2ce2860dd872
Revises: a83c28ee0a01
Create Date: 2024-12-22 12:27:01.026249

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table
from migrations.columns import add_column, drop_column, alter_columns
from migrations.constraints import create_constraints, create_constraint, drop_constraint
from migrations.indexes import create_indexes, drop_indexes, create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '2ce2860dd872'
down_revision = 'a83c28ee0a01'
branch_labels = None
depends_on = None


UPLOAD_ELEMENT_STATUS_TABLE_CONFIG = {
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
            'name': 'pk_upload_element_status',
            'columns': ['id'],
        },
    ],
    'with_rowid': True,
}

UPLOAD_ELEMENT_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'upload_id',
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
            'name': 'pk_upload_element',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_upload_element_upload_id_upload',
            'columns': ['upload_id'],
            'references': ['upload.id'],
        }, {
            'name': 'fk_upload_element_illust_url_id_illust_url',
            'columns': ['illust_url_id'],
            'references': ['illust_url.id'],
        }, {
            'name': 'fk_upload_element_status_id_upload_element_status',
            'columns': ['status_id'],
            'references': ['upload_element_status.id'],
        },
    ],
    'with_rowid': True,
}

UPLOAD_URL_TABLE_CONFIG = {
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
            'name': 'upload_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_upload_url',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_upload_url_upload_id_upload',
            'columns': ['upload_id'],
            'references': ['upload.id'],
        },
    ],
    'with_rowid': True,
}

UPLOAD_TABLE_UPGRADE = """
DELETE FROM upload
WHERE upload.request_url IS NOT NULL
"""

ERROR_TABLE_UPGRADE_CREATE = """
CREATE TABLE error_temp (
	id	INTEGER NOT NULL,
	module	TEXT NOT NULL,
	message	TEXT NOT NULL,
	created	INTEGER NOT NULL,
	post_id	INTEGER,
	subscription_id	INTEGER,
	subscription_element_id	INTEGER,
	upload_id	INTEGER,
	download_id	INTEGER,
	download_element_id	INTEGER,
	CONSTRAINT pk_error PRIMARY KEY(id),
	CONSTRAINT fk_error_download_element_id_download_element FOREIGN KEY(download_element_id) REFERENCES download_element(id),
	CONSTRAINT fk_error_download_id_download FOREIGN KEY(download_id) REFERENCES download(id),
	CONSTRAINT fk_error_post_id_post FOREIGN KEY(post_id) REFERENCES post(id),
	CONSTRAINT fk_error_subscription_element_id_subscription FOREIGN KEY(subscription_element_id) REFERENCES subscription_element(id),
	CONSTRAINT fk_error_subscription_id_subscription FOREIGN KEY(subscription_id) REFERENCES subscription(id),
	CONSTRAINT fk_error_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload(id),
	CONSTRAINT ck_error_attachments CHECK(((post_id IS NULL) + (subscription_id IS NULL) + (subscription_element_id IS NULL) + (upload_id IS NULL) + (download_id IS NULL) + (download_element_id IS NULL)) IN (5, 6))
)
"""

ERROR_TABLE_UPGRADE_INSERT = """
INSERT INTO error_temp(id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, download_id, download_element_id)
SELECT id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, download_id, download_element_id
FROM error
"""

ERROR_TABLE_UPGRADE_DROP = """
DROP TABLE error
"""

ERROR_TABLE_UPGRADE_RENAME = """
ALTER TABLE error_temp RENAME TO error
"""

ERROR_TABLE_DOWNGRADE_CREATE = """
CREATE TABLE error_temp (
	id	INTEGER NOT NULL,
	module	TEXT NOT NULL,
	message	TEXT NOT NULL,
	created	INTEGER NOT NULL,
	post_id	INTEGER,
	subscription_id	INTEGER,
	subscription_element_id	INTEGER,
	upload_id	INTEGER,
	upload_element_id	INTEGER,
	download_id	INTEGER,
	download_element_id	INTEGER,
	CONSTRAINT pk_error PRIMARY KEY(id),
	CONSTRAINT fk_error_download_element_id_download_element FOREIGN KEY(download_element_id) REFERENCES download_element(id),
	CONSTRAINT fk_error_download_id_download FOREIGN KEY(download_id) REFERENCES download(id),
	CONSTRAINT fk_error_post_id_post FOREIGN KEY(post_id) REFERENCES post(id),
	CONSTRAINT fk_error_subscription_element_id_subscription FOREIGN KEY(subscription_element_id) REFERENCES subscription_element(id),
	CONSTRAINT fk_error_subscription_id_subscription FOREIGN KEY(subscription_id) REFERENCES subscription(id),
	CONSTRAINT fk_error_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload(id),
	CONSTRAINT fk_error_upload_element_id_upload_element FOREIGN KEY(upload_element_id) REFERENCES upload_element(id),
	CONSTRAINT ck_error_attachments CHECK(((post_id IS NULL) + (subscription_id IS NULL) + (subscription_element_id IS NULL) + (upload_id IS NULL) + (upload_element_id IS NULL) + (download_id IS NULL) + (download_element_id IS NULL)) IN (6, 7))
)
"""

ERROR_TABLE_DOWNGRADE_INSERT = """
INSERT INTO error_temp(id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id, download_id, download_element_id)
SELECT id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, NULL, download_id, download_element_id
FROM error
"""

ERROR_TABLE_DOWNGRADE_DROP = """
DROP TABLE error
"""

ERROR_TABLE_DOWNGRADE_RENAME = """
ALTER TABLE error_temp RENAME TO error
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Upgrading errors table")
    # Trying to drop the check constraint before recreating it removes the named aspect of all of the constraints, so do it manually for now
    connection.execute(ERROR_TABLE_UPGRADE_CREATE)
    connection.execute(ERROR_TABLE_UPGRADE_INSERT)
    connection.execute(ERROR_TABLE_UPGRADE_DROP)
    connection.execute(ERROR_TABLE_UPGRADE_RENAME)
    create_indexes('error', [
        ('ix_error_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ('ix_error_download_id', ['download_id'], False, {'sqlite_where': 'download_id IS NOT NULL'}),
        ('ix_error_download_element_id', ['download_element_id'], False, {'sqlite_where': 'download_element_id IS NOT NULL'}),
        ('ix_error_upload_id', ['upload_id'], False, {'sqlite_where': 'upload_id IS NOT NULL'}),
        ('ix_error_subscription_id', ['subscription_id'], False, {'sqlite_where': 'subscription_id IS NOT NULL'}),
        ('ix_error_subscription_element_id', ['subscription_element_id'], False, {'sqlite_where': 'subscription_element_id IS NOT NULL'}),
    ])

    print("Upgrading uploads table")
    connection.execute(UPLOAD_TABLE_UPGRADE)
    drop_column('upload', 'request_url')
    alter_columns('upload', [
        ('illust_url_id', 'INTEGER', {'nullable': False}),
        ('media_filepath', 'TEXT', {'nullable': False}),
    ], batch_kwargs={'naming': True})

    print ("Dropping tables")
    drop_table('upload_element_status')
    drop_table('upload_element')
    drop_table('upload_url')


def downgrade_():
    connection = op.get_bind()

    print("Creating tables")
    create_table('upload_element_status', **UPLOAD_ELEMENT_STATUS_TABLE_CONFIG)
    create_table('upload_element', **UPLOAD_ELEMENT_TABLE_CONFIG)
    create_table('upload_url', **UPLOAD_URL_TABLE_CONFIG)

    print("Downgrading uploads table")
    alter_columns('upload', [
        ('illust_url_id', 'INTEGER', {'nullable': True}),
        ('media_filepath', 'TEXT', {'nullable': True}),
    ], batch_kwargs={'naming': True})
    add_column('upload', 'request_url', 'TEXT')

    print("Downgrading errors table")
    connection.execute(ERROR_TABLE_DOWNGRADE_CREATE)
    connection.execute(ERROR_TABLE_DOWNGRADE_INSERT)
    connection.execute(ERROR_TABLE_DOWNGRADE_DROP)
    connection.execute(ERROR_TABLE_DOWNGRADE_RENAME)
    create_indexes('error', [
        ('ix_error_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ('ix_error_download_id', ['download_id'], False, {'sqlite_where': 'download_id IS NOT NULL'}),
        ('ix_error_download_element_id', ['download_element_id'], False, {'sqlite_where': 'download_element_id IS NOT NULL'}),
        ('ix_error_upload_id', ['upload_id'], False, {'sqlite_where': 'upload_id IS NOT NULL'}),
        ('ix_error_upload_element_id', ['upload_id'], False, {'sqlite_where': 'upload_element_id IS NOT NULL'}),
        ('ix_error_subscription_id', ['subscription_id'], False, {'sqlite_where': 'subscription_id IS NOT NULL'}),
        ('ix_error_subscription_element_id', ['subscription_element_id'], False, {'sqlite_where': 'subscription_element_id IS NOT NULL'}),
    ])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
