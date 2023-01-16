# MIGRATIONS/VERSIONS/C93C2735DC1C_ADD_REVERSE_INDEXES_ON_SECONDARY_TABLES.PY
"""Add reverse indexes on secondary tables

Revision ID: c93c2735dc1c
Revises: bf612e5a12a4
Create Date: 2022-10-18 11:34:10.528084

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'c93c2735dc1c'
down_revision = 'bf612e5a12a4'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    create_index('artist_notations', 'ix_artist_notations_notation_id_artist_id', ['notation_id', 'artist_id'], False)
    create_index('illust_notations', 'ix_illust_notations_notation_id_illust_id', ['notation_id', 'illust_id'], False)
    create_index('post_illust_urls', 'ix_post_illust_urls_illust_url_id_post_id', ['illust_url_id', 'post_id'], False)
    create_index('post_notations', 'ix_post_notations_notation_id_post_id', ['notation_id', 'post_id'], False)
    create_index('post_errors', 'ix_post_errors_error_id_post_id', ['error_id', 'post_id'], False)
    create_index('upload_errors', 'ix_upload_errors_error_id_upload_id', ['error_id', 'upload_id'], False)
    create_index('upload_element_errors', 'ix_upload_element_errors_error_id_upload_element_id', ['error_id', 'upload_element_id'], False)
    create_index('subscription_errors', 'ix_subscription_errors_error_id_subscription_id', ['error_id', 'subscription_id'], False)
    create_index('subscription_element_errors', 'ix_subscription_element_errors_error_id_subscription_element_id', ['error_id', 'subscription_element_id'], False)


def downgrade_():
    drop_index('artist_notations', 'ix_artist_notations_notation_id_artist_id')
    drop_index('illust_notations', 'ix_illust_notations_notation_id_illust_id')
    drop_index('post_illust_urls', 'ix_post_illust_urls_illust_url_id_post_id')
    drop_index('post_notations', 'ix_post_notations_notation_id_post_id')
    drop_index('post_errors', 'ix_post_errors_error_id_post_id')
    drop_index('upload_errors', 'ix_upload_errors_error_id_upload_id')
    drop_index('upload_element_errors', 'ix_upload_element_errors_error_id_upload_element_id')
    drop_index('subscription_errors', 'ix_subscription_errors_error_id_subscription_id')
    drop_index('subscription_element_errors', 'ix_subscription_element_errors_error_id_subscription_element_id')
