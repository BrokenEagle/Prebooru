# MIGRATIONS/VERSIONS/110801DFDB7C_DROP_UPLOAD_POSTS_TABLE.PY
"""Drop upload posts table

Revision ID: 110801dfdb7c
Revises: 1628b38aae0a
Create Date: 2022-10-17 18:02:54.644541

"""

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '110801dfdb7c'
down_revision = '1628b38aae0a'
branch_labels = None
depends_on = None

UPLOAD_POSTS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'upload_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'post_id',
            'type': 'Integer',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_upload_posts',
            'columns': ['upload_id', 'post_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_upload_posts_upload_id_upload',
            'columns': ['upload_id'],
            'references': ['upload.id'],
        }, {
            'name': 'fk_upload_posts_post_id_post',
            'columns': ['post_id'],
            'references': ['post.id'],
        },
    ],
    'with_rowid': False,
}

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_table('upload_posts')


def downgrade_():
    create_table('upload_posts', **UPLOAD_POSTS_TABLE_CONFIG)
