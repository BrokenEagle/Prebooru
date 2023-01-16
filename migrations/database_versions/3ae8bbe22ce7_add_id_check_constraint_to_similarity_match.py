# MIGRATIONS/VERSIONS/3AE8BBE22CE7_ADD_ID_CHECK_CONSTRAINT_TO_SIMILARITY_MATCH.PY
"""Add ID check constraint to similarity match

Revision ID: 3ae8bbe22ce7
Revises: fe28448f97f4
Create Date: 2022-12-19 14:06:18.752210

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table, remove_temp_tables
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '3ae8bbe22ce7'
down_revision = 'fe28448f97f4'
branch_labels = None
depends_on = None

SIMILARITY_MATCH_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'forward_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'reverse_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'score',
            'type': 'Float',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_similarity_match',
            'columns': ['forward_id', 'reverse_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_similarity_match_forward_id_post',
            'columns': ['forward_id'],
            'references': ['post.id'],
        }, {
            'name': 'fk_similarity_match_reverse_id_post',
            'columns': ['reverse_id'],
            'references': ['post.id'],
        },
    ],
    'ck_config': [
        {
            'name': 'ck_similarity_match_id_order',
            'value': 'forward_id < reverse_id',
        },
    ],
    'with_rowid': False,
}

INSERT_STATEMENT = """
INSERT INTO similarity_match_t(forward_id, reverse_id, score) 
SELECT DISTINCT
    CASE WHEN similarity_match.forward_id < similarity_match.reverse_id THEN similarity_match.forward_id ELSE similarity_match.reverse_id END forward_id_1,
    CASE WHEN similarity_match.forward_id < similarity_match.reverse_id THEN similarity_match.reverse_id ELSE similarity_match.forward_id END reverse_id_1,
    similarity_match.score AS score_1
FROM similarity_match
WHERE true
ON CONFLICT DO NOTHING
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['similarity_match_t'], add_precursor=False)
    create_table('similarity_match_t', **SIMILARITY_MATCH_TABLE_CONFIG)
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    conn.execute(sa.text(INSERT_STATEMENT))
    drop_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id')
    drop_table('similarity_match')
    op.rename_table('similarity_match_t', 'similarity_match')
    create_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id', ['reverse_id', 'forward_id'], True)


def downgrade_():
    remove_temp_tables(['similarity_match'])
    drop_constraint('similarity_match', 'ck_similarity_match_id_order', 'check')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
