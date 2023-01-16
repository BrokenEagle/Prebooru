# MIGRATIONS/VERSIONS/5EF65FE1B761_ADD_MULTIPLE_INDEXES_TO_FOREIGN_PRIMARY_KEYS.PY
"""Add multiple indexes to foreign/primary keys

Revision ID: 5ef65fe1b761
Revises: d00857ade29f
Create Date: 2022-10-16 21:10:43.896744

"""
# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.indexes import create_index, create_indexes, drop_index, drop_indexes

# revision identifiers, used by Alembic.
revision = '5ef65fe1b761'
down_revision = 'd00857ade29f'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['image_hash', 'similarity_match', 'site_data', 'subscription', 'subscription_element'])
    create_index('image_hash', 'ix_image_hash_post_id', ['post_id'], False)
    create_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id', ['reverse_id', 'forward_id'], True)
    create_index('site_data', 'ix_site_data_illust_id', ['illust_id'], False)
    create_index('subscription', 'ix_subscription_artist_id', ['artist_id'], False)
    create_indexes('subscription_element',
        [
            ('ix_subscription_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
            ('ix_subscription_element_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ]
    )



def downgrade_():
    remove_temp_tables(['image_hash', 'similarity_match', 'site_data', 'subscription', 'subscription_element'])
    drop_index('image_hash', 'ix_image_hash_post_id')
    drop_index('similarity_match', 'ix_similarity_match_reverse_id_forward_id')
    drop_index('site_data', 'ix_site_data_illust_id')
    drop_index('subscription', 'ix_subscription_artist_id')
    drop_indexes('subscription_element', ['ix_subscription_element_md5', 'ix_subscription_element_post_id'])
