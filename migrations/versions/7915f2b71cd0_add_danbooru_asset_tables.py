# MIGRATIONS/VERSIONS/7915F2B71CD0_ADD_DANBOORU_ASSET_TABLES.PY
"""Add danbooru asset tables

Revision ID: 7915f2b71cd0
Revises: fa670b30cd07
Create Date: 2022-12-06 15:18:39.526146

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7915f2b71cd0'
down_revision = 'fa670b30cd07'
branch_labels = None
depends_on = None

DANBOORU_ASSET_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'asset_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'model_id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'post_id',
            'type': 'Integer',
            'nullable': True,
        }, {
            'name': 'illust_id',
            'type': 'Integer',
            'nullable': True,
        }, {
            'name': 'artist_id',
            'type': 'Integer',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_danbooru_asset',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_danbooru_asset_model_id_danbooru_asset_model',
            'columns': ['model_id'],
            'references': ['danbooru_asset_model.id'],
        }, {
            'name': 'fk_danbooru_asset_post_id_post',
            'columns': ['post_id'],
            'references': ['post.id'],
        }, {
            'name': 'fk_danbooru_asset_illust_id_illust',
            'columns': ['illust_id'],
            'references': ['illust.id'],
        }, {
            'name': 'fk_danbooru_asset_artist_id_artist',
            'columns': ['artist_id'],
            'references': ['artist.id'],
        },
    ],
    'with_rowid': True,
}

DANBOORU_ASSET_MODEL_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'Integer',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'String',
            'nullable': False,
        }, 
    ],
    'pk_config': [
        {
            'name': 'pk_danbooru_asset_model',
            'columns': ['id'],
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
    create_table('danbooru_asset_model', **DANBOORU_ASSET_MODEL_TABLE_CONFIG)
    create_table('danbooru_asset', **DANBOORU_ASSET_TABLE_CONFIG)


def downgrade_():
    drop_table('danbooru_asset')
    drop_table('danbooru_asset_model')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
