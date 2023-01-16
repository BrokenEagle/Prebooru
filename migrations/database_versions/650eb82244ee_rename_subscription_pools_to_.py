"""Rename subscription pools to subscriptions

Revision ID: 650eb82244ee
Revises: 86a07c28c96a
Create Date: 2022-09-10 15:42:43.017529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '650eb82244ee'
down_revision = '86a07c28c96a'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_N_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


def upgrade_():
    print("Dropping constraints")
    print("\tSubscription Pool")
    with op.batch_alter_table('subscription_pool', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_pool', type_='primary')
        batch_op.drop_constraint('fk_subscription_pool_artist_id_artist', type_='foreignkey')

    print("\tSubscription Pool Element")
    with op.batch_alter_table('subscription_pool_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_pool_element', type_='primary')
        batch_op.drop_constraint('fk_subscription_pool_element_illust_url_id_illust_url', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_pool_element_pool_id_subscription_pool', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_pool_element_post_id_post', type_='foreignkey')

    print("\tSubscription Pool Errors")
    with op.batch_alter_table('subscription_pool_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_pool_errors', type_='primary')
        batch_op.drop_constraint('fk_subscription_pool_errors_subscription_pool_id_subscription_pool', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_pool_errors_error_id_error', type_='foreignkey')

    print("\tSubscription Pool Element Errors")
    with op.batch_alter_table('subscription_pool_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_pool_element_errors', type_='primary')
        batch_op.drop_constraint('fk_subscription_pool_element_errors_subscription_pool_element_id_subscription_pool_element', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_pool_element_errors_error_id_error', type_='foreignkey')

    print("Renaming tables")
    op.rename_table('subscription_pool', 'subscription')
    op.rename_table('subscription_pool_element', 'subscription_element')
    op.rename_table('subscription_pool_errors', 'subscription_errors')
    op.rename_table('subscription_pool_element_errors', 'subscription_element_errors')

    print("Changing field names")
    print("\tSubscription Element")
    with op.batch_alter_table('subscription_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('pool_id', new_column_name='subscription_id')

    print("\tSubscription Errors")
    with op.batch_alter_table('subscription_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('subscription_pool_id', new_column_name='subscription_id')

    print("\tSubscription Element Errors")
    with op.batch_alter_table('subscription_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('subscription_pool_element_id', new_column_name='subscription_element_id')

    print("Adding constraints")
    print("\tSubscription")
    with op.batch_alter_table('subscription', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription', ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_artist_id_artist'), 'artist', ['artist_id'], ['id'])

    print("\tSubscription Element")
    with op.batch_alter_table('subscription_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_element', ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_element_illust_url_id_illust_url'), 'illust_url', ['illust_url_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_element_subscription_id_subscription'), 'subscription', ['subscription_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_element_post_id_post'), 'post', ['post_id'], ['id'])

    print("\tSubscription Errors")
    with op.batch_alter_table('subscription_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_errors', ['subscription_id', 'error_id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_errors_subscription_id_subscription'), 'subscription', ['subscription_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_errors_error_id_error'), 'error', ['error_id'], ['id'])

    print("\tSubscription Element Errors")
    with op.batch_alter_table('subscription_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_element_errors', ['subscription_element_id', 'error_id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_element_errors_subscription_element_id_subscription_element'), 'subscription_element', ['subscription_element_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_element_errors_error_id_error'), 'error', ['error_id'], ['id'])


def downgrade_():
    print("Dropping constraints")
    print("\tSubscription")
    with op.batch_alter_table('subscription', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription', type_='primary')
        batch_op.drop_constraint('fk_subscription_artist_id_artist', type_='foreignkey')

    print("\tSubscription Element")
    with op.batch_alter_table('subscription_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_element', type_='primary')
        batch_op.drop_constraint('fk_subscription_element_illust_url_id_illust_url', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_element_subscription_id_subscription', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_element_post_id_post', type_='foreignkey')

    print("\tSubscription Errors")
    with op.batch_alter_table('subscription_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_errors', type_='primary')
        batch_op.drop_constraint('fk_subscription_errors_subscription_id_subscription', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_errors_error_id_error', type_='foreignkey')

    print("\tSubscription Element Errors")
    with op.batch_alter_table('subscription_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('pk_subscription_element_errors', type_='primary')
        batch_op.drop_constraint('fk_subscription_element_errors_subscription_element_id_subscription_element', type_='foreignkey')
        batch_op.drop_constraint('fk_subscription_element_errors_error_id_error', type_='foreignkey')

    print("Renaming tables")
    op.rename_table('subscription', 'subscription_pool')
    op.rename_table('subscription_element', 'subscription_pool_element')
    op.rename_table('subscription_errors', 'subscription_pool_errors')
    op.rename_table('subscription_element_errors', 'subscription_pool_element_errors')

    print("Changing field names")
    print("\tSubscription Pool Element")
    with op.batch_alter_table('subscription_pool_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('subscription_id', new_column_name='pool_id')

    print("\tSubscription Pool Errors")
    with op.batch_alter_table('subscription_pool_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('subscription_id', new_column_name='subscription_pool_id')

    print("\tSubscription Pool Element Errors")
    with op.batch_alter_table('subscription_pool_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('subscription_element_id', new_column_name='subscription_pool_element_id')


    print("Adding constraints")
    print("\tSubscription Pool")
    with op.batch_alter_table('subscription_pool', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_pool', ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_artist_id_artist'), 'artist', ['artist_id'], ['id'])

    print("\tSubscription Pool Element")
    with op.batch_alter_table('subscription_pool_element', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_pool_element', ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_element_illust_url_id_illust_url'), 'illust_url', ['illust_url_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_element_pool_id_subscription_pool'), 'subscription_pool', ['pool_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_element_post_id_post'), 'post', ['post_id'], ['id'])

    print("\tSubscription Pool Errors")
    with op.batch_alter_table('subscription_pool_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_pool_errors', ['subscription_pool_id', 'error_id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_errors_subscription_pool_id_subscription_pool'), 'subscription_pool', ['subscription_pool_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_errors_error_id_error'), 'error', ['error_id'], ['id'])

    print("\tSubscription Pool Element Errors")
    with op.batch_alter_table('subscription_pool_element_errors', schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.create_primary_key('pk_subscription_pool_element_errors', ['subscription_pool_element_id', 'error_id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_element_errors_subscription_pool_element_id_subscription_pool_element'), 'subscription_pool_element', ['subscription_pool_element_id'], ['id'])
        batch_op.create_foreign_key(batch_op.f('fk_subscription_pool_element_errors_error_id_error'), 'error', ['error_id'], ['id'])
