# MIGRATIONS/VERSIONS/6B803CE90831_ADD_FOREIGN_KEY_CONSTRAINTS_TO_ENUM_DEPENDANT_TABLES.PY
"""Add foreign key constraints to enum dependant tables

Revision ID: 6b803ce90831
Revises: 8058d124fd2b
Create Date: 2022-11-23 15:15:07.818402

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.tables import remove_temp_tables
from migrations.columns import alter_column
from migrations.constraints import create_constraints, drop_constraints, create_constraint, drop_constraint
from migrations.indexes import create_indexes, drop_indexes, create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '6b803ce90831'
down_revision = '8058d124fd2b'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['api_data', 'archive', 'artist', 'illust', 'illust_url', 'post', 'subscription',
                        'subscription_element', 'upload', 'upload_element', 'pool_element', 'site_data', 'tag'])

    print("Upgrading ApiData table")
    op.alter_column('api_data', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    op.alter_column('api_data', 'site', existing_type=sa.INTEGER, **{'new_column_name': 'site_id'})
    create_constraints('api_data', [
        ('fk_api_data_type_id_api_data_type', 'foreignkey', ('api_data_type', ['type_id'], ['id'])),
        ('fk_api_data_site_id_site_descriptor', 'foreignkey', ('site_descriptor', ['site_id'], ['id'])),
    ])

    print("Upgrading Archive table")
    op.alter_column('archive', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    create_constraint('archive', 'fk_archive_type_id_archive_type', 'foreignkey', ('archive_type', ['type_id'], ['id']))

    print("Upgrading Artist table")
    op.alter_column('artist', 'site', existing_type=sa.INTEGER, **{'new_column_name': 'site_id'})
    create_constraint('artist', 'fk_artist_site_id_site_descriptor', 'foreignkey', ('site_descriptor', ['site_id'], ['id']))

    print("Upgrading Illust table")
    op.alter_column('illust', 'site', existing_type=sa.INTEGER, **{'new_column_name': 'site_id'})
    create_constraint('illust', 'fk_illust_site_id_site_descriptor', 'foreignkey', ('site_descriptor', ['site_id'], ['id']))

    print("Upgrading IllustUrl table")
    op.alter_column('illust_url', 'site', existing_type=sa.INTEGER, **{'new_column_name': 'site_id'})
    op.alter_column('illust_url', 'sample_site', existing_type=sa.INTEGER, **{'new_column_name': 'sample_site_id'})
    create_constraints('illust_url', [
        ('fk_illust_url_site_id_site_descriptor', 'foreignkey', ('site_descriptor', ['site_id'], ['id'])),
        ('fk_illust_url_sample_site_id_sample_site_descriptor', 'foreignkey', ('site_descriptor', ['sample_site_id'], ['id'])),
    ])

    print("Upgrading Post table")
    op.alter_column('post', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    create_constraint('post', 'fk_post_type_id_post_type', 'foreignkey', ('post_type', ['type_id'], ['id']))

    print("Upgrading Subscription table")
    op.alter_column('subscription', 'status', existing_type=sa.INTEGER, **{'new_column_name': 'status_id'})
    create_constraint('subscription', 'fk_subscription_status_id_subscription_status', 'foreignkey', ('subscription_status', ['status_id'], ['id']))

    print("Upgrading SubscriptionElement table")
    op.alter_column('subscription_element', 'status', existing_type=sa.INTEGER, **{'new_column_name': 'status_id'})
    op.alter_column('subscription_element', 'keep', existing_type=sa.INTEGER, **{'new_column_name': 'keep_id'})
    # Have to recreate partial indexes anyways, and this prevents the indexes from having to be recreated twice
    drop_indexes('subscription_element', ['ix_subscription_element_md5', 'ix_subscription_element_post_id'])
    create_constraints('subscription_element', [
        ('fk_subscription_element_status_id_subscription_element_status', 'foreignkey', ('subscription_element_status', ['status_id'], ['id'])),
        ('fk_subscription_element_keep_id_subscription_element_keep', 'foreignkey', ('subscription_element_keep', ['keep_id'], ['id'])),
    ])
    create_indexes('subscription_element', [
        ('ix_subscription_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
        ('ix_subscription_element_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])

    print("Upgrading Upload table")
    op.alter_column('upload', 'status', existing_type=sa.INTEGER, **{'new_column_name': 'status_id'})
    create_constraint('upload', 'fk_upload_status_id_upload_status', 'foreignkey', ('upload_status', ['status_id'], ['id']))

    print("Upgrading UploadElement table")
    op.alter_column('upload_element', 'status', existing_type=sa.INTEGER, **{'new_column_name': 'status_id'})
    create_constraint('upload_element', 'fk_upload_element_status_id_upload_element_status', 'foreignkey', ('upload_element_status', ['status_id'], ['id']))
    drop_index('upload_element', 'ix_upload_element_md5')
    create_index('upload_element', 'ix_upload_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')

    print("Upgrading PoolElement table")
    op.alter_column('pool_element', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    # Same deal as above with the partial indexes
    drop_indexes('pool_element', ['ix_pool_element_illust_id_pool_id', 'ix_pool_element_notation_id_pool_id', 'ix_pool_element_post_id_pool_id'])
    create_constraint('pool_element', 'fk_pool_element_type_id_pool_element_type', 'foreignkey', ('pool_element_type', ['type_id'], ['id']))
    create_indexes('pool_element', [
        ('ix_pool_element_illust_id_pool_id', ['illust_id', 'pool_id'], True, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_pool_element_notation_id_pool_id', ['notation_id', 'pool_id'], True, {'sqlite_where': 'notation_id IS NOT NULL'}),
        ('ix_pool_element_post_id_pool_id', ['post_id', 'pool_id'], True, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])

    print("Upgrading SiteData table")
    op.alter_column('site_data', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    create_constraint('site_data', 'fk_site_data_type_id_site_data_type', 'foreignkey', ('site_data_type', ['type_id'], ['id']))

    print("Upgrading Tag table")
    op.alter_column('tag', 'type', existing_type=sa.INTEGER, **{'new_column_name': 'type_id'})
    create_constraint('tag', 'fk_tag_type_id_tag_type', 'foreignkey', ('tag_type', ['type_id'], ['id']))


def downgrade_():
    remove_temp_tables(['api_data'])
    print("Downgrading ApiData table")
    drop_constraints('api_data', [
        ('fk_api_data_type_id_api_data_type', 'foreignkey'),
        ('fk_api_data_site_id_site_descriptor', 'foreignkey'),
    ])
    op.alter_column('api_data', 'site_id', existing_type=sa.INTEGER, **{'new_column_name': 'site'})
    op.alter_column('api_data', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})

    print("Downgrading Archive table")
    drop_constraint('archive', 'fk_archive_type_id_archive_type', 'foreignkey')
    op.alter_column('archive', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})

    print("Downgrading Artist table")
    drop_constraint('artist', 'fk_artist_site_id_site_descriptor', 'foreignkey')
    op.alter_column('artist', 'site_id', existing_type=sa.INTEGER, **{'new_column_name': 'site'})

    print("Downgrading Illust table")
    drop_constraint('illust', 'fk_illust_site_id_site_descriptor', 'foreignkey')
    op.alter_column('illust', 'site_id', existing_type=sa.INTEGER, **{'new_column_name': 'site'})

    print("Downgrading IllustUrl table")
    drop_constraints('illust_url', [
        ('fk_illust_url_site_id_site_descriptor', 'foreignkey'),
        ('fk_illust_url_sample_site_id_sample_site_descriptor', 'foreignkey'),
    ])
    op.alter_column('illust_url', 'site_id', existing_type=sa.INTEGER, **{'new_column_name': 'site'})
    op.alter_column('illust_url', 'sample_site_id', existing_type=sa.INTEGER, **{'new_column_name': 'sample_site'})

    print("Downgrading Post table")
    drop_constraint('post', 'fk_post_type_id_post_type', 'foreignkey')
    op.alter_column('post', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})

    print("Downgrading Subscription table")
    drop_constraint('subscription', 'fk_subscription_status_id_subscription_status', 'foreignkey')
    op.alter_column('subscription', 'status_id', existing_type=sa.INTEGER, **{'new_column_name': 'status'})

    print("Downgrading SubscriptionElement table")
    # Have to recreate partial indexes
    drop_indexes('subscription_element', ['ix_subscription_element_md5', 'ix_subscription_element_post_id'])
    drop_constraints('subscription_element', [
        ('fk_subscription_element_status_id_subscription_element_status', 'foreignkey'),
        ('fk_subscription_element_keep_id_subscription_element_keep', 'foreignkey'),
    ])
    create_indexes('subscription_element', [
        ('ix_subscription_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
        ('ix_subscription_element_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])
    op.alter_column('subscription_element', 'status_id', existing_type=sa.INTEGER, **{'new_column_name': 'status'})
    op.alter_column('subscription_element', 'keep_id', existing_type=sa.INTEGER, **{'new_column_name': 'keep'})

    print("Downgrading Upload table")
    drop_constraint('upload', 'fk_upload_status_id_upload_status', 'foreignkey')
    op.alter_column('upload', 'status_id', existing_type=sa.INTEGER, **{'new_column_name': 'status'})

    print("Downgrading UploadElement table")
    drop_constraint('upload_element', 'fk_upload_element_status_id_upload_element_status', 'foreignkey')
    op.alter_column('upload_element', 'status_id', existing_type=sa.INTEGER, **{'new_column_name': 'status'})
    drop_index('upload_element', 'ix_upload_element_md5')
    create_index('upload_element', 'ix_upload_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')

    print("Downgrading PoolElement table")
    # Same with the partial indexes
    drop_indexes('pool_element', ['ix_pool_element_illust_id_pool_id', 'ix_pool_element_notation_id_pool_id', 'ix_pool_element_post_id_pool_id'])
    drop_constraint('pool_element', 'fk_pool_element_type_id_pool_element_type', 'foreignkey')
    create_indexes('pool_element', [
        ('ix_pool_element_illust_id_pool_id', ['illust_id', 'pool_id'], True, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_pool_element_notation_id_pool_id', ['notation_id', 'pool_id'], True, {'sqlite_where': 'notation_id IS NOT NULL'}),
        ('ix_pool_element_post_id_pool_id', ['post_id', 'pool_id'], True, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])
    op.alter_column('pool_element', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})

    print("Downgrading SiteData table")
    drop_constraint('site_data', 'fk_site_data_type_id_site_data_type', 'foreignkey')
    op.alter_column('site_data', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})

    print("Downgrading Tag table")
    drop_constraint('tag', 'fk_tag_type_id_tag_type', 'foreignkey')
    op.alter_column('tag', 'type_id', existing_type=sa.INTEGER, **{'new_column_name': 'type'})


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
