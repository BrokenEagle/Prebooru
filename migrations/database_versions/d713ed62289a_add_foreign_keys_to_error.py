# MIGRATIONS/VERSIONS/D713ED62289A_ADD_FOREIGN_KEYS_TO_ERROR.PY
"""Add foreign keys to error

Revision ID: d713ed62289a
Revises: b311f123b313
Create Date: 2023-01-16 13:08:32.398649

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_indexes, drop_indexes, create_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd713ed62289a'
down_revision = 'b311f123b313'
branch_labels = None
depends_on = None

CREATE_UPGRADE_ERROR_TABLE = """
CREATE TABLE error_t (
	id INTEGER NOT NULL, 
	module TEXT NOT NULL, 
	message TEXT NOT NULL, 
	created INTEGER NOT NULL, 
	post_id INTEGER,
	subscription_id INTEGER,
	subscription_element_id INTEGER,
	upload_id INTEGER,
	upload_element_id INTEGER,
	CONSTRAINT pk_error PRIMARY KEY (id),
	CONSTRAINT fk_error_post_id_post FOREIGN KEY(post_id) REFERENCES post (id),
	CONSTRAINT fk_error_subscription_id_subscription FOREIGN KEY(subscription_id) REFERENCES subscription (id),
	CONSTRAINT fk_error_subscription_element_id_subscription_element FOREIGN KEY(subscription_element_id) REFERENCES subscription_element (id),
	CONSTRAINT fk_error_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload (id),
	CONSTRAINT fk_error_upload_element_id_upload_element FOREIGN KEY(upload_element_id) REFERENCES upload_element (id),
	CONSTRAINT ck_error_attachments CHECK(
		(("post_id" IS NULL) + ("subscription_id" IS NULL) + ("subscription_element_id" IS NULL) + ("upload_id" IS NULL) + ("upload_element_id" IS NULL)) in (4, 5)
	)
)
"""

INSERT_UPGRADE_ERROR_TABLE = """
INSERT INTO error_t(id, module, message, created, post_id, subscription_id, subscription_element_id, upload_id, upload_element_id)
SELECT error.id, error.module, error.message, error.created, post_errors.post_id, subscription_errors.subscription_id,
       subscription_element_errors.subscription_element_id, upload_errors.upload_id, upload_element_errors.upload_element_id
FROM error
OUTER LEFT JOIN post_errors ON error.id = post_errors.error_id
OUTER LEFT JOIN subscription_errors ON error.id = subscription_errors.error_id
OUTER LEFT JOIN subscription_element_errors ON error.id = subscription_element_errors.error_id
OUTER LEFT JOIN upload_errors ON error.id = upload_errors.error_id
OUTER LEFT JOIN upload_element_errors ON error.id = upload_element_errors.error_id
"""

CREATE_DOWNGRADE_ERROR_TABLE = """
CREATE TABLE error_t (
	id INTEGER NOT NULL, 
	module TEXT NOT NULL, 
	message TEXT NOT NULL, 
	created INTEGER NOT NULL, 
	CONSTRAINT pk_error PRIMARY KEY (id)
)
"""

CREATE_DOWNGRADE_POST_ERRORS_TABLE = """
CREATE TABLE post_errors (
	post_id INTEGER NOT NULL, 
	error_id INTEGER NOT NULL, 
	CONSTRAINT pk_post_errors PRIMARY KEY (post_id, error_id), 
	CONSTRAINT fk_post_errors_post_id_post FOREIGN KEY(post_id) REFERENCES post (id), 
	CONSTRAINT fk_post_errors_error_id_error FOREIGN KEY(error_id) REFERENCES error (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_SUBSCRIPTION_ERRORS_TABLE = """
CREATE TABLE subscription_errors (
	subscription_id INTEGER NOT NULL, 
	error_id INTEGER NOT NULL, 
	CONSTRAINT pk_subscription_errors PRIMARY KEY (subscription_id, error_id), 
	CONSTRAINT fk_subscription_errors_subscription_id_subscription FOREIGN KEY(subscription_id) REFERENCES subscription (id), 
	CONSTRAINT fk_subscription_errors_error_id_error FOREIGN KEY(error_id) REFERENCES error (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_SUBSCRIPTION_ELEMENT_ERRORS_TABLE = """
CREATE TABLE subscription_element_errors (
	subscription_element_id INTEGER NOT NULL, 
	error_id INTEGER NOT NULL, 
	CONSTRAINT pk_subscription_element_errors PRIMARY KEY (subscription_element_id, error_id), 
	CONSTRAINT fk_subscription_element_errors_subscription_element_id_subscription_element FOREIGN KEY(subscription_element_id) REFERENCES subscription_element (id), 
	CONSTRAINT fk_subscription_element_errors_error_id_error FOREIGN KEY(error_id) REFERENCES error (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_UPLOAD_ERRORS_TABLE = """
CREATE TABLE upload_errors (
	upload_id INTEGER NOT NULL, 
	error_id INTEGER NOT NULL, 
	CONSTRAINT pk_upload_errors PRIMARY KEY (upload_id, error_id), 
	CONSTRAINT fk_upload_errors_upload_id_upload FOREIGN KEY(upload_id) REFERENCES upload (id), 
	CONSTRAINT fk_upload_errors_error_id_error FOREIGN KEY(error_id) REFERENCES error (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_UPLOAD_ELEMENT_ERRORS_TABLE = """
CREATE TABLE upload_element_errors (
	upload_element_id INTEGER NOT NULL, 
	error_id INTEGER NOT NULL, 
	CONSTRAINT pk_upload_element_errors PRIMARY KEY (upload_element_id, error_id), 
	CONSTRAINT fk_upload_element_errors_upload_element_id_upload_element FOREIGN KEY(upload_element_id) REFERENCES upload_element (id), 
	CONSTRAINT fk_upload_element_errors_error_id_error FOREIGN KEY(error_id) REFERENCES error (id)
) WITHOUT ROWID
"""

INSERT_DOWNGRADE_ERROR_TABLE = """
INSERT INTO error_t(id, module, message, created)
SELECT id, module, message, created
FROM error
"""

INSERT_DOWNGRADE_POST_ERRORS_TABLE = """
INSERT INTO post_errors(post_id, error_id)
SELECT error.post_id, error.id AS error_id
FROM error
WHERE error.post_id IS NOT NULL
"""

INSERT_DOWNGRADE_SUBSCRIPTION_ERRORS_TABLE = """
INSERT INTO subscription_errors(subscription_id, error_id)
SELECT error.subscription_id, error.id AS error_id
FROM error
WHERE error.subscription_id IS NOT NULL
"""

INSERT_DOWNGRADE_SUBSCRIPTION_ELEMENT_ERRORS_TABLE = """
INSERT INTO subscription_element_errors(subscription_element_id, error_id)
SELECT error.subscription_element_id, error.id AS error_id
FROM error
WHERE error.subscription_element_id IS NOT NULL
"""

INSERT_DOWNGRADE_UPLOAD_ERRORS_TABLE = """
INSERT INTO upload_errors(upload_id, error_id)
SELECT error.upload_id, error.id AS error_id
FROM error
WHERE error.upload_id IS NOT NULL
"""

INSERT_DOWNGRADE_UPLOAD_ELEMENT_ERRORS_TABLE = """
INSERT INTO upload_element_errors(upload_element_id, error_id)
SELECT error.upload_element_id, error.id AS error_id
FROM error
WHERE error.upload_element_id IS NOT NULL
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_indexes('error', [
        'ix_post_errors_error_id_post_id',
        'ix_subscription_errors_error_id_subscription_id',
        'ix_subscription_element_errors_error_id_subscription_element_id',
        'ix_upload_errors_error_id_upload_id',
        'ix_upload_element_errors_error_id_upload_element_id',
    ])
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_UPGRADE_ERROR_TABLE.strip()))
    conn.execute(sa.text(INSERT_UPGRADE_ERROR_TABLE.strip()))
    op.drop_table('error')
    op.rename_table('error_t', 'error')
    op.drop_table('post_errors')
    op.drop_table('subscription_errors')
    op.drop_table('subscription_element_errors')
    op.drop_table('upload_errors')
    op.drop_table('upload_element_errors')
    create_indexes('error', [
        ('ix_error_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ('ix_error_subscription_id', ['subscription_id'], False, {'sqlite_where': 'subscription_id IS NOT NULL'}),
        ('ix_error_subscription_element_id', ['subscription_element_id'], False, {'sqlite_where': 'subscription_element_id IS NOT NULL'}),
        ('ix_error_upload_id', ['upload_id'], False, {'sqlite_where': 'upload_id IS NOT NULL'}),
        ('ix_error_upload_element_id', ['upload_element_id'], False, {'sqlite_where': 'upload_element_id IS NOT NULL'}),
    ])


def downgrade_():
    drop_indexes('error', [
        'ix_error_post_id',
        'ix_error_subscription_id',
        'ix_error_subscription_element_id',
        'ix_error_upload_id',
        'ix_error_upload_element_id',
    ])
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_DOWNGRADE_ERROR_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_POST_ERRORS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_SUBSCRIPTION_ERRORS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_SUBSCRIPTION_ELEMENT_ERRORS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_UPLOAD_ERRORS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_UPLOAD_ELEMENT_ERRORS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_ERROR_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_POST_ERRORS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_SUBSCRIPTION_ERRORS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_SUBSCRIPTION_ELEMENT_ERRORS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_UPLOAD_ERRORS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_UPLOAD_ELEMENT_ERRORS_TABLE.strip()))
    op.drop_table('error')
    op.rename_table('error_t', 'error')
    create_index('post_errors', 'ix_post_errors_error_id_post_id', ['error_id', 'post_id'], False)
    create_index('upload_errors', 'ix_upload_errors_error_id_upload_id', ['error_id', 'upload_id'], False)
    create_index('upload_element_errors', 'ix_upload_element_errors_error_id_upload_element_id', ['error_id', 'upload_element_id'], False)
    create_index('subscription_errors', 'ix_subscription_errors_error_id_subscription_id', ['error_id', 'subscription_id'], False)
    create_index('subscription_element_errors', 'ix_subscription_element_errors_error_id_subscription_element_id', ['error_id', 'subscription_element_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

