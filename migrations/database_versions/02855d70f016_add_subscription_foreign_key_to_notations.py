# MIGRATIONS/VERSIONS/02855D70F016_ADD_SUBSCRIPTION_FOREIGN_KEY_TO_SUBSCRIPTIONS.PY
"""Add subscription foreign key to subscriptions

Revision ID: 02855d70f016
Revises: 7262282fa74a
Create Date: 2023-06-30 11:32:24.216655

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_indexes, drop_indexes
from migrations.tables import remove_temp_tables

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '02855d70f016'
down_revision = '7262282fa74a'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['notation'])

    drop_indexes('notation', ['ix_notation_booru_id', 'ix_notation_artist_id', 'ix_notation_illust_id', 'ix_notation_post_id'])

    with op.batch_alter_table('notation', schema=None) as batch_op:
        drop_constraint(None, 'ck_notation_attachments', 'check', batch_op=batch_op)
        add_column(None, 'subscription_id', 'Integer', batch_op=batch_op)
        create_constraint(None, 'fk_notation_subscription_id_subscription', 'foreignkey', ('subscription', ['subscription_id'], ['id']), batch_op=batch_op)
        create_constraint(None, 'ck_notation_attachments', 'check', ["""(("post_id" IS NULL) + ("illust_id" IS NULL) + ("artist_id" IS NULL) + ("booru_id" IS NULL) + ("subscription_id" IS NULL) + "no_pool") IN (5, 6)"""], batch_op=batch_op)

    create_indexes('notation', [
        ('ix_notation_subscription_id', ['subscription_id'], False, {'sqlite_where': 'subscription_id IS NOT NULL'}),
        ('ix_notation_booru_id', ['booru_id'], False, {'sqlite_where': 'booru_id IS NOT NULL'}),
        ('ix_notation_artist_id', ['artist_id'], False, {'sqlite_where': 'artist_id IS NOT NULL'}),
        ('ix_notation_illust_id', ['illust_id'], False, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_notation_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])


def downgrade_():
    remove_temp_tables(['notation'])

    drop_indexes('notation', ['ix_notation_subscription_id', 'ix_notation_booru_id', 'ix_notation_artist_id', 'ix_notation_illust_id', 'ix_notation_post_id'])

    with op.batch_alter_table('notation', schema=None) as batch_op:
        drop_constraint(None, 'ck_notation_attachments', 'check', batch_op=batch_op)
        drop_column(None, 'subscription_id', batch_op=batch_op)
        create_constraint(None, 'ck_notation_attachments', 'check', ["""(("post_id" IS NULL) + ("illust_id" IS NULL) + ("artist_id" IS NULL) + ("booru_id" IS NULL) + "no_pool") IN (4, 5)"""], batch_op=batch_op)

    create_indexes('notation', [
        ('ix_notation_booru_id', ['booru_id'], False, {'sqlite_where': 'booru_id IS NOT NULL'}),
        ('ix_notation_artist_id', ['artist_id'], False, {'sqlite_where': 'artist_id IS NOT NULL'}),
        ('ix_notation_illust_id', ['illust_id'], False, {'sqlite_where': 'illust_id IS NOT NULL'}),
        ('ix_notation_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
    ])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

