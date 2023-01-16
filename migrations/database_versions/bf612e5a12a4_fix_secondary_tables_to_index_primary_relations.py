# MIGRATIONS/VERSIONS/BF612E5A12A4_FIX_SECONDARY_TABLES_TO_INDEX_PRIMARY_RELATIONS.PY
"""Fix secondary tables to index primary relations

Revision ID: bf612e5a12a4
Revises: 110801dfdb7c
Create Date: 2022-10-18 03:12:49.272840

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'bf612e5a12a4'
down_revision = '110801dfdb7c'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    batch_kwargs = {
        'table_kwargs': {
            'sqlite_with_rowid': False,
        },
        'recreate': 'always',
    }
    remove_temp_tables(['artist_names', 'artist_site_accounts', 'artist_profiles', 'artist_notations', 'illust_tags',
                        'illust_commentaries', 'post_illust_urls', 'post_tags'])
    drop_constraint('artist_names', 'pk_artist_names', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('artist_id', 'label_id')]
    create_constraint('artist_names', 'pk_artist_names', 'primary', ['artist_id', 'label_id'], batch_kwargs=kwargs)
    drop_constraint('artist_site_accounts', 'pk_artist_site_accounts', 'primary')
    create_constraint('artist_site_accounts', 'pk_artist_site_accounts', 'primary', ['artist_id', 'label_id'], batch_kwargs=kwargs)
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('artist_id', 'description_id')]
    drop_constraint('artist_profiles', 'pk_artist_profiles', 'primary')
    create_constraint('artist_profiles', 'pk_artist_profiles', 'primary', ['artist_id', 'description_id'], batch_kwargs=kwargs)
    drop_constraint('artist_notations', 'pk_artist_notations', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('artist_id', 'notation_id')]
    create_constraint('artist_notations', 'pk_artist_notations', 'primary', ['artist_id', 'notation_id'], batch_kwargs=kwargs)
    drop_constraint('illust_tags', 'pk_illust_tags', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('illust_id', 'tag_id')]
    create_constraint('illust_tags', 'pk_illust_tags', 'primary', ['illust_id', 'tag_id'], batch_kwargs=kwargs)
    drop_constraint('illust_commentaries', 'pk_illust_commentaries', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('illust_id', 'description_id')]
    create_constraint('illust_commentaries', 'pk_illust_commentaries', 'primary', ['illust_id', 'description_id'], batch_kwargs=kwargs)
    drop_constraint('post_illust_urls', 'pk_post_illust_urls', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('illust_id', 'illust_url_id')]
    create_constraint('post_illust_urls', 'pk_post_illust_urls', 'primary', ['post_id', 'illust_url_id'], batch_kwargs=kwargs)
    drop_constraint('post_tags', 'pk_post_tags', 'primary')
    kwargs = batch_kwargs.copy()
    kwargs['partial_reordering'] = [('post_id', 'tag_id')]
    create_constraint('post_tags', 'pk_post_tags', 'primary', ['post_id', 'tag_id'], batch_kwargs=kwargs)


def downgrade_():
    pass
