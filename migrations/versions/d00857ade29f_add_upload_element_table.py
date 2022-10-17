# MIGRATIONS/VERSIONS/D00857ADE29F_ADD_UPLOAD_ELEMENT_TABLE.PY
"""Add upload element table

Revision ID: d00857ade29f
Revises: dd461c6e511a
Create Date: 2022-10-14 17:07:47.530138

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables, create_table, drop_table
from migrations.indexes import create_indexes, drop_indexes


# revision identifiers, used by Alembic.
revision = 'd00857ade29f'
down_revision = 'dd461c6e511a'
branch_labels = None
depends_on = None

ELEMENT_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'upload_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'illust_url_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'md5',
            'type': 'String',
            'nullable': True,
        }, {
            'name': 'status',
            'type': 'Integer',
            'nullable': False,
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
        },
    ],
    'with_rowid': True,
}

ELEMENT_ERRORS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'upload_element_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'error_id',
            'type': 'Integer',
            'nullable': False,
        }, 
    ],
    'pk_config': [
        {
            'name': 'pk_upload_element',
            'columns': ['upload_element_id', 'error_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_upload_element_errors_upload_element_id_upload_element',
            'columns': ['upload_element_id'],
            'references': ['upload_element.id'],
        }, {
            'name': 'fk_upload_element_errors_error_id_error',
            'columns': ['error_id'],
            'references': ['error.id'],
        },
    ],
    'with_rowid': False,
}


# ## GLOBAL VARIABLES

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['upload_element', 'upload_element_errors'], False)
    create_table('upload_element', **ELEMENT_TABLE_CONFIG)
    create_indexes('upload_element', [
        ('ix_upload_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
        ('ix_upload_element_upload_id', ['upload_id'], False, {'sqlite_where': 'upload_id IS NOT NULL'}),
    ])
    create_table('upload_element_errors', **ELEMENT_ERRORS_TABLE_CONFIG)


def downgrade_():
    drop_table('upload_element_errors')
    drop_indexes('upload_element', ['ix_upload_element_md5', 'ix_upload_element_upload_id'])
