# MIGRATIONS/VERSIONS/5D148349FDBF_ADD_POST_FOREIGN_KEY_TO_ILLUST_URL.PY
"""Add post foreign key to illust url

Revision ID: 5d148349fdbf
Revises: 84f2ac2664a2
Create Date: 2023-01-16 18:54:38.200061

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_indexes, create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '5d148349fdbf'
down_revision = '84f2ac2664a2'
branch_labels = None
depends_on = None

CREATE_UPGRADE_ILLUST_URL_TABLE = """
CREATE TABLE illust_url_t (
	id INTEGER NOT NULL,
	site_id INTEGER NOT NULL,
	url TEXT NOT NULL,
	width INTEGER NOT NULL,
	height INTEGER NOT NULL,
	"order" INTEGER NOT NULL,
	illust_id INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	sample_site_id INTEGER,
	sample_url TEXT,
	post_id INTEGER,
	CONSTRAINT pk_illust_url PRIMARY KEY (id),
	CONSTRAINT fk_illust_url_illust_id_illust FOREIGN KEY(illust_id) REFERENCES illust (id),
	CONSTRAINT fk_illust_url_site_id_site_descriptor FOREIGN KEY(site_id) REFERENCES site_descriptor (id),
	CONSTRAINT fk_illust_url_sample_site_id_sample_site_descriptor FOREIGN KEY(sample_site_id) REFERENCES site_descriptor (id),
	CONSTRAINT fk_illust_url_post_id_post FOREIGN KEY(post_id) REFERENCES post (id)
)
"""

INSERT_UPGRADE_ILLUST_URL_TABLE = """
INSERT INTO illust_url_t(id, site_id, url, width, height, "order", illust_id, active, sample_site_id, sample_url, post_id)
SELECT illust_url.id, illust_url.site_id, illust_url.url, illust_url.width, illust_url.height, illust_url."order",
       illust_url.illust_id, illust_url.active, illust_url.sample_site_id, illust_url.sample_url, post_illust_urls.post_id
FROM illust_url
OUTER LEFT JOIN post_illust_urls ON illust_url.id = post_illust_urls.illust_url_id
"""

CREATE_DOWNGRADE_ILLUST_URL_TABLE = """
CREATE TABLE illust_url_t (
	id INTEGER NOT NULL,
	site_id INTEGER NOT NULL,
	url TEXT NOT NULL,
	width INTEGER NOT NULL,
	height INTEGER NOT NULL,
	"order" INTEGER NOT NULL,
	illust_id INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	sample_site_id INTEGER,
	sample_url TEXT,
	CONSTRAINT pk_illust_url PRIMARY KEY (id),
	CONSTRAINT fk_illust_url_illust_id_illust FOREIGN KEY(illust_id) REFERENCES illust (id),
	CONSTRAINT fk_illust_url_site_id_site_descriptor FOREIGN KEY(site_id) REFERENCES site_descriptor (id),
	CONSTRAINT fk_illust_url_sample_site_id_sample_site_descriptor FOREIGN KEY(sample_site_id) REFERENCES site_descriptor (id)
)
"""

CREATE_DOWNGRADE_POST_ILLUST_URLS_TABLE = """
CREATE TABLE post_illust_urls (
	post_id INTEGER NOT NULL, 
	illust_url_id INTEGER NOT NULL, 
	CONSTRAINT pk_post_illust_urls PRIMARY KEY (post_id, illust_url_id), 
	CONSTRAINT fk_post_illust_urls_post_id_post FOREIGN KEY(post_id) REFERENCES post (id), 
	CONSTRAINT fk_post_illust_urls_illust_url_id_illust_url FOREIGN KEY(illust_url_id) REFERENCES illust_url (id)
) WITHOUT ROWID
"""

INSERT_DOWNGRADE_ILLUST_URL_TABLE = """
INSERT INTO illust_url_t(id, site_id, url, width, height, "order", illust_id, active, sample_site_id, sample_url)
SELECT illust_url.id, illust_url.site_id, illust_url.url, illust_url.width, illust_url.height, illust_url."order",
       illust_url.illust_id, illust_url.active, illust_url.sample_site_id, illust_url.sample_url
FROM illust_url
"""

INSERT_DOWNGRADE_POST_ILLUST_URLS_TABLE = """
INSERT INTO post_illust_urls(post_id, illust_url_id)
SELECT illust_url.post_id, illust_url.id AS illust_url_id
FROM illust_url
WHERE illust_url.post_id IS NOT NULL
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_index('post_illust_urls', 'ix_post_illust_urls_illust_url_id_post_id')
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_UPGRADE_ILLUST_URL_TABLE.strip()))
    conn.execute(sa.text(INSERT_UPGRADE_ILLUST_URL_TABLE.strip()))
    op.drop_table('illust_url')
    op.drop_table('post_illust_urls')
    op.rename_table('illust_url_t', 'illust_url')
    create_indexes('illust_url', [
        ('ix_illust_url_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ('ix_illust_url_illust_id', ['illust_id'], False),
    ])


def downgrade_():
    drop_index('illust_url', 'ix_illust_url_post_id')
    conn = op.get_bind()
    conn.execute(sa.text(CREATE_DOWNGRADE_ILLUST_URL_TABLE.strip()))
    conn.execute(sa.text(CREATE_DOWNGRADE_POST_ILLUST_URLS_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_ILLUST_URL_TABLE.strip()))
    conn.execute(sa.text(INSERT_DOWNGRADE_POST_ILLUST_URLS_TABLE.strip()))
    op.drop_table('illust_url')
    op.rename_table('illust_url_t', 'illust_url')
    create_index('post_illust_urls', 'ix_post_illust_urls_illust_url_id_post_id', ['illust_url_id', 'post_id'], True)
    create_index('illust_url', 'ix_illust_url_post_id', ['illust_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

