# MIGRATIONS/VERSIONS/D2C16D9D9233_CHANGE_SIMILARITY_MATCH_REVERSE_ID_INDEX.PY
"""Change similarity match reverse_id index

Revision ID: d2c16d9d9233
Revises: 2ce2860dd872
Create Date: 2024-12-23 21:46:49.381944

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd2c16d9d9233'
down_revision = '2ce2860dd872'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id')
    create_index('similarity_match', 'ix_similarity_match_reverse_id', ['reverse_id'], False)


def downgrade_():
    drop_index('similarity_match', 'ix_similarity_match_reverse_id')
    create_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id', ['reverse_id', 'forward_id'], True)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

