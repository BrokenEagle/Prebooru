"""Modify and rename similarity pool element

Revision ID: 0d7ddfdeb870
Revises: 3ca72b51c7cd
Create Date: 2022-10-09 10:08:22.512788

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.indexes import drop_index, create_index

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '0d7ddfdeb870'
down_revision = '3ca72b51c7cd'
branch_labels = None
depends_on = None

UPGRADE_TABLE = """
CREATE TABLE "similarity_match" (
\tforward_id INTEGER NOT NULL, 
\treverse_id INTEGER NOT NULL, 
\tscore FLOAT NOT NULL, 
\tCONSTRAINT pk_similarity_match PRIMARY KEY (forward_id, reverse_id), 
\tCONSTRAINT fk_similarity_match_forward_id_post FOREIGN KEY(forward_id) REFERENCES post (id), 
\tCONSTRAINT fk_similarity_match_reverse_id_post FOREIGN KEY(reverse_id) REFERENCES post (id) 
) WITHOUT ROWID
"""

UPGRADE_INSERT = """
INSERT INTO similarity_match (forward_id, reverse_id, score)
SELECT
    similarity_pool_element.pool_id AS forward_id,
    similarity_pool_element.post_id AS reverse_id,
    similarity_pool_element.score
FROM similarity_pool_element
WHERE similarity_pool_element.main IS true"""

DOWNGRADE_TABLE = """
CREATE TABLE "similarity_pool_element" (
\tid INTEGER NOT NULL, 
\tpool_id INTEGER NOT NULL, 
\tsibling_id INTEGER, 
\tpost_id INTEGER NOT NULL, 
\tscore FLOAT NOT NULL, 
\tmain BOOLEAN NOT NULL, 
\tCONSTRAINT pk_similarity_pool_element PRIMARY KEY (id), 
\tCONSTRAINT fk_similarity_pool_element_post_id_post FOREIGN KEY(post_id) REFERENCES post (id), 
\tCONSTRAINT fk_similarity_pool_element_sibling_id_similarity_pool_element FOREIGN KEY(sibling_id) REFERENCES similarity_pool_element (id), 
\tCONSTRAINT fk_similarity_pool_element_pool_id_similarity_pool FOREIGN KEY(pool_id) REFERENCES similarity_pool (id)
)"""

DOWNGRADE_INSERT1 = """
INSERT INTO similarity_pool_element (pool_id, post_id, score, main)
SELECT
    similarity_match.forward_id AS pool_id,
    similarity_match.reverse_id AS post_id,
    similarity_match.score,
    true
FROM similarity_match"""

DOWNGRADE_INSERT2 = """
INSERT INTO similarity_pool_element (pool_id, post_id, score, main)
SELECT
    similarity_match.reverse_id AS pool_id,
    similarity_match.forward_id AS post_id,
    similarity_match.score,
    false
FROM similarity_match"""

DOWNGRADE_UPDATE = """
UPDATE
    similarity_pool_element
SET 
    sibling_id = spe.id
FROM
    similarity_pool_element as spe
WHERE
    similarity_pool_element.pool_id == spe.post_id
AND
    similarity_pool_element.post_id == spe.pool_id"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['similarity_match'], False)
    connection = op.get_bind()
    connection.execute(UPGRADE_TABLE)
    connection.execute(UPGRADE_INSERT)
    drop_index('similarity_pool_element', 'ix_similarity_pool_element_pool_id')
    op.drop_table('similarity_pool_element')



def downgrade_():
    remove_temp_tables(['similarity_pool_element'], False)
    connection = op.get_bind()
    connection.execute(DOWNGRADE_TABLE)
    connection.execute(DOWNGRADE_INSERT1)
    connection.execute(DOWNGRADE_INSERT2)
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute(DOWNGRADE_UPDATE)
    connection.execute("PRAGMA foreign_keys=ON")
    create_index('similarity_pool_element', 'ix_similarity_pool_element_pool_id', ['pool_id'], False)
    op.drop_table('similarity_match')
