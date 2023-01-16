# MIGRATIONS/VERSIONS/3CA72B51C7CD
"""Convert secondary tables to without rowid

Revision ID: 3ca72b51c7cd
Revises: 1799b5ade686
Create Date: 2022-10-08 20:28:52.823256

"""

# PYTHON IMPORTS
import re

# EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# PACKAGE IMPORTS
from migrations.tables import remove_temp_tables


# GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '3ca72b51c7cd'
down_revision = '1799b5ade686'
branch_labels = None
depends_on = None

secondary_tables = ['artist_names', 'artist_site_accounts', 'artist_profiles', 'artist_notations', 'booru_names',
                    'booru_artists', 'illust_tags', 'illust_commentaries', 'illust_notations', 'post_illust_urls',
                    'post_errors', 'post_notations', 'post_tags', 'subscription_errors', 'subscription_element_errors',
                    'upload_urls', 'upload_errors', 'upload_posts']


# FUNCTIONS

def convert_secondary_tables(connection, name, temp_name, regex, replace):
    print("Converting secondary table:", name)
    table, sqlscheme = connection.execute(f"SELECT name,sql FROM 'main'.sqlite_master WHERE name='{name}';").fetchone()
    norowid_schema_statement = re.sub(regex, replace, sqlscheme, 1, re.IGNORECASE | re.DOTALL)
    connection.execute(norowid_schema_statement)
    lines = [line.strip() for line in re.split(r'\n+', re.sub('\t', ' ', sqlscheme))[1: 3]]
    fields = [re.match(r"""[\w'"]+""", line).group(0).replace('"', "").replace("'", "") for line in lines]
    insert_into_statement = f"INSERT INTO {temp_name} ({fields[0]}, {fields[1]}) SELECT {fields[0]}, {fields[1]} FROM {name}"
    connection.execute(insert_into_statement)
    op.drop_table(name)
    op.rename_table(temp_name, name)


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['__prebooru_temp_' + name for name in secondary_tables], False)
    connection = op.get_bind()
    for name in secondary_tables:
        temp_name = '__prebooru_temp_' + name
        convert_secondary_tables(connection, name, temp_name, r"""^(create table )([\w'"]+)(.*)$""",  rf"\1{temp_name}\3 WITHOUT ROWID")


def downgrade_():
    remove_temp_tables(['__prebooru_temp_' + name for name in secondary_tables], False)
    connection = op.get_bind()
    for name in secondary_tables:
        temp_name = '__prebooru_temp_' + name
        convert_secondary_tables(connection, name, temp_name, r"""^(create table )([\w'"]+)(.*)WITHOUT ROWID$""",  rf"\1{temp_name}\3")
