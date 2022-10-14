# MIGRATIONS/VERSIONS/BFE4356C79E9_ADD_DUPLICATE_POST_TABLE.PY
"""Add duplicate_post table

Revision ID: bfe4356c79e9
Revises: dd461c6e511a
Create Date: 2022-10-13 13:34:07.651851

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables, create_table, drop_table
from migrations.indexes import create_indexes, drop_indexes


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'bfe4356c79e9'
down_revision = 'dd461c6e511a'
branch_labels = None
depends_on = None

TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'post_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'upload_id',
            'type': 'Integer',
            'nullable': True,
        }, {
            'name': 'subscription_element_id',
            'type': 'Integer',
            'nullable': True,
        }, {
            'name': 'type',
            'type': 'Integer',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_duplicate_post',
            'columns': 'id',
        },
    ],
    'fk_config': [
        {
            'name': 'fk_duplicate_post_post_id_post',
            'columns': ['post_id'],
            'references': ['post.id'],
        }, {
            'name': 'fk_duplicate_post_subscription_element_id_subscription_element',
            'columns': ['upload_id'],
            'references': ['upload.id'],
        }, {
            'name': 'fk_duplicate_post_upload_id_upload',
            'columns': ['subscription_element_id'],
            'references': ['subscription_element.id'],
        },
    ],
    'ck_config': [
        {
            'name': 'ck_duplicate_post_null_check',
            'value': '((upload_id IS NOT NULL and 1) + (subscription_element_id IS NOT NULL and 1)) == 1',
        },
    ],
    'with_rowid': True,
}

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['duplicate_post'], False)
    create_table('duplicate_post', **TABLE_CONFIG)
    create_indexes('duplicate_post', [
        ('ix_duplicate_post_post_id', ['post_id'], False),
        ('ix_duplicate_post_upload_id_post_id', ['upload_id', 'post_id'], True, {'sqlite_where': 'upload_id IS NOT NULL'}),
        ('ix_duplicate_post_subscription_element_id_post_id', ['subscription_element_id', 'post_id'], True, {'sqlite_where': 'subscription_element_id IS NOT NULL'}),
    ])


def downgrade_():
    drop_indexes('duplicate_post', ['ix_duplicate_post_post_id',
                                    'ix_duplicate_post_upload_id_post_id',
                                    'ix_duplicate_post_subscription_element_id_post_id'])
    drop_table('duplicate_post')
