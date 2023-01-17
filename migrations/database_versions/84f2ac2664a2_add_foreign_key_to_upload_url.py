# MIGRATIONS/VERSIONS/84F2AC2664A2_ADD_FOREIGN_KEY_TO_UPLOAD_URL.PY
"""Add foreign key to upload url

Revision ID: 84f2ac2664a2
Revises: d713ed62289a
Create Date: 2023-01-16 16:14:47.942024

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '84f2ac2664a2'
down_revision = 'd713ed62289a'
branch_labels = None
depends_on = None

CREATE_UPGRADE_UPLOAD_URL_TABLE = """
CREATE TABLE upload_url_t (
	id INTEGER NOT NULL, 
	url TEXT NOT NULL, 
	upload_id INTEGER NOT NULL, 
	CONSTRAINT pk_upload_url PRIMARY KEY (id),
	CONSTRAINT fk_upload_url_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload (id)
)
"""

INSERT_UPGRADE_UPLOAD_URL_TABLE = """
INSERT INTO upload_url_t(id, url, upload_id)
SELECT upload_url.id, upload_url.url, upload_urls.upload_id
FROM upload_url
INNER JOIN upload_urls ON upload_urls.upload_url_id = upload_url.id
"""

CREATE_DOWNGRADE_UPLOAD_URL_TABLE = """
CREATE TABLE upload_url_t (
	id INTEGER NOT NULL, 
	url VARCHAR(255) NOT NULL, 
	CONSTRAINT pk_upload_url PRIMARY KEY (id)
)
"""

CREATE_DOWNGRADE_UPLOAD_URLS_TABLE = """
CREATE TABLE upload_urls (
	upload_id INTEGER NOT NULL, 
	upload_url_id INTEGER NOT NULL, 
	CONSTRAINT pk_upload_urls PRIMARY KEY (upload_id, upload_url_id), 
	CONSTRAINT fk_upload_urls_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload (id), 
	CONSTRAINT fk_upload_urls_upload_url_id_upload_url FOREIGN KEY(upload_url_id) REFERENCES upload_url (id)
) WITHOUT ROWID
"""

INSERT_DOWNGRADE_UPLOAD_URL_TABLE = """
INSERT INTO upload_url_t(id, url)
SELECT id, url
FROM upload_url
"""

INSERT_DOWNGRADE_UPLOAD_URLS_TABLE = """
INSERT INTO upload_urls(upload_id, upload_url_id)
SELECT upload_url.upload_id, upload_url.id AS upload_url_id
FROM upload_url
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_UPGRADE_UPLOAD_URL_TABLE.strip()))
    conn.execute(sa.text(INSERT_UPGRADE_UPLOAD_URL_TABLE.strip()))
    op.drop_table('upload_url')
    op.drop_table('upload_urls')
    op.rename_table('upload_url_t', 'upload_url')
    create_index('upload_url', 'ix_upload_url_upload_id', ['upload_id'], False)


def downgrade_():
    drop_index('upload_url', 'ix_upload_url_upload_id')
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_DOWNGRADE_UPLOAD_URL_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_UPLOAD_URLS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_UPLOAD_URL_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_UPLOAD_URLS_TABLE.strip()))
    op.drop_table('upload_url')
    op.rename_table('upload_url_t', 'upload_url')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

