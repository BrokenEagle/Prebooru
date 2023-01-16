# MIGRATIONS/VERSIONS/B311F123B313_ADD_FOREIGN_KEYS_TO_NOTATION.PY
"""Add foreign keys to notation

Revision ID: b311f123b313
Revises: 3ae8bbe22ce7
Create Date: 2023-01-11 20:49:40.731179

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_indexes, drop_indexes, create_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'b311f123b313'
down_revision = '8a5d77ca02ff'
branch_labels = None
depends_on = None

CREATE_UPGRADE_NOTATION_TABLE = """
CREATE TABLE notation_t (
	id INTEGER NOT NULL,
	body TEXT NOT NULL,
	created INTEGER NOT NULL,
	updated INTEGER NOT NULL,
	booru_id INTEGER,
	artist_id INTEGER,
	illust_id INTEGER,
	post_id INTEGER,
	no_pool BOOLEAN NOT NULL,
	CONSTRAINT pk_notation PRIMARY KEY (id),
	CONSTRAINT fk_notation_post_id_post FOREIGN KEY(post_id) REFERENCES post (id),
	CONSTRAINT fk_notation_artist_id_artist FOREIGN KEY(artist_id) REFERENCES artist (id),
	CONSTRAINT fk_notation_illust_id_illust FOREIGN KEY(illust_id) REFERENCES illust (id),
	CONSTRAINT fk_notation_booru_id_booru FOREIGN KEY(booru_id) REFERENCES booru (id),
	CONSTRAINT ck_notation_no_pool_boolean CHECK(no_pool = 0 or no_pool = 1),
	CONSTRAINT ck_notation_attachments CHECK(
		((post_id IS NULL) + (illust_id IS NULL) + (artist_id IS NULL) + (booru_id IS NULL) + no_pool) in (4, 5)
	)
)
"""

INSERT_UPGRADE_NOTATION_TABLE = """
INSERT INTO notation_t(id, body, created, updated, booru_id, artist_id, illust_id, post_id, no_pool)
SELECT notation.id, notation.body, notation.created, notation.updated, NULL AS booru_id, artist_notations.artist_id,
       illust_notations.illust_id, post_notations.post_id, pool_element.pool_id IS NULL AS no_pool
FROM notation
OUTER LEFT JOIN artist_notations ON notation.id = artist_notations.notation_id
OUTER LEFT JOIN illust_notations ON notation.id = illust_notations.notation_id
OUTER LEFT JOIN post_notations ON notation.id = post_notations.notation_id
OUTER LEFT JOIN pool_element ON notation.id = pool_element.notation_id
"""

CREATE_DOWNGRADE_NOTATION_TABLE = """
CREATE TABLE notation_t (
	id INTEGER NOT NULL,
	body TEXT NOT NULL,
	created INTEGER NOT NULL,
	updated INTEGER NOT NULL,
	CONSTRAINT pk_notation PRIMARY KEY (id)
)
"""

CREATE_DOWNGRADE_ARTIST_NOTATIONS_TABLE = """
CREATE TABLE artist_notations (
	artist_id INTEGER NOT NULL,
	notation_id INTEGER NOT NULL,
	CONSTRAINT pk_artist_notations PRIMARY KEY (artist_id, notation_id),
	CONSTRAINT fk_artist_notations_notation_id_notation FOREIGN KEY(notation_id) REFERENCES notation (id),
	CONSTRAINT fk_artist_notations_artist_id_artist FOREIGN KEY(artist_id) REFERENCES artist (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_ILLUST_NOTATIONS_TABLE = """
CREATE TABLE illust_notations (
	illust_id INTEGER NOT NULL,
	notation_id INTEGER NOT NULL,
	CONSTRAINT pk_illust_notations PRIMARY KEY (illust_id, notation_id),
	CONSTRAINT fk_illust_notations_notation_id_notation FOREIGN KEY(notation_id) REFERENCES notation (id),
	CONSTRAINT fk_illust_notations_illust_id_illust FOREIGN KEY(illust_id) REFERENCES illust (id)
) WITHOUT ROWID
"""

CREATE_DOWNGRADE_POST_NOTATIONS_TABLE = """
CREATE TABLE post_notations (
	post_id INTEGER NOT NULL,
	notation_id INTEGER NOT NULL,
	CONSTRAINT pk_post_notations PRIMARY KEY (post_id, notation_id),
	CONSTRAINT fk_post_notations_notation_id_notation FOREIGN KEY(notation_id) REFERENCES notation (id),
	CONSTRAINT fk_post_notations_post_id_post FOREIGN KEY(post_id) REFERENCES post (id)
) WITHOUT ROWID
"""

INSERT_DOWNGRADE_NOTATION_TABLE = """
INSERT INTO notation_t(id, body, created, updated)
SELECT id, body, created, updated
FROM notation
"""

INSERT_DOWNGRADE_ARTIST_NOTATIONS_TABLE = """
INSERT INTO artist_notations(artist_id, notation_id)
SELECT notation.artist_id, notation.id AS notation_id
FROM notation
WHERE notation.artist_id IS NOT NULL
"""

INSERT_DOWNGRADE_ILLUST_NOTATIONS_TABLE = """
INSERT INTO illust_notations(illust_id, notation_id)
SELECT notation.illust_id, notation.id AS notation_id
FROM notation
WHERE notation.illust_id IS NOT NULL
"""

INSERT_DOWNGRADE_POST_NOTATIONS_TABLE = """
INSERT INTO post_notations(post_id, notation_id)
SELECT notation.post_id, notation.id AS notation_id
FROM notation
WHERE notation.post_id IS NOT NULL
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_indexes('notation', [
        'ix_artist_notations_notation_id_artist_id',
        'ix_illust_notations_notation_id_illust_id',
        'ix_post_notations_notation_id_post_id',
    ])
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_UPGRADE_NOTATION_TABLE.strip()))
    conn.execute(sa.text(INSERT_UPGRADE_NOTATION_TABLE.strip()))
    op.drop_table('notation')
    op.rename_table('notation_t', 'notation')
    op.drop_table('artist_notations')
    op.drop_table('illust_notations')
    op.drop_table('post_notations')
    create_indexes('notation', [
        ('ix_notation_booru_id', ['booru_id'], False, {'sqlite_where': 'booru_id IS NOT NULL'}),
        ('ix_notation_artist_id', ['artist_id'], False, {'sqlite_where': 'artist_id IS NOT NULL'}),
        ('ix_notation_illust_id', ['illust_id'], False, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_notation_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])


def downgrade_():
    drop_indexes('notation', [
        'ix_notation_booru_id',
        'ix_notation_artist_id',
        'ix_notation_illust_id',
        'ix_notation_post_id',
    ])
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_DOWNGRADE_NOTATION_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_ARTIST_NOTATIONS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_ILLUST_NOTATIONS_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_POST_NOTATIONS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_NOTATION_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_ARTIST_NOTATIONS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_ILLUST_NOTATIONS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_POST_NOTATIONS_TABLE.strip()))
    op.drop_table('notation')
    op.rename_table('notation_t', 'notation')
    create_index('artist_notations', 'ix_artist_notations_notation_id_artist_id', ['notation_id', 'artist_id'], False)
    create_index('illust_notations', 'ix_illust_notations_notation_id_illust_id', ['notation_id', 'illust_id'], False)
    create_index('post_notations', 'ix_post_notations_notation_id_post_id', ['notation_id', 'post_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
