"""Change ApiData storage to compressed JSON

Revision ID: cf6510a015f0
Revises: cee25e958cb0
Create Date: 2022-09-23 05:40:07.242683

"""
# ## PYTHON IMPORTS
import json
import zlib

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'cf6510a015f0'
down_revision = 'cee25e958cb0'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    t_api_data = sa.Table(
        'api_data',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('data', sa.JSON),
        sa.Column('temp', sa.BLOB),
    )

    print("Adding temp column")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.BLOB(), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        api_data = connection.execute(sa.select([t_api_data.c.id, t_api_data.c.data]).limit(1000).offset(index * 1000)).fetchall()
        for datum in api_data:
            string_value = json.dumps(datum[1], ensure_ascii=False, separators=(',', ':'))
            encoded_value = string_value.encode('UTF')
            compressed_value = zlib.compress(encoded_value)
            connection.execute(t_api_data.update().where(t_api_data.c.id == datum[0]).values(
                temp=compressed_value,
                ))
        if len(api_data):
            print(f"api data #{api_data[0][0]} - api data #{api_data[-1][0]}")
        if len(api_data) < 1000:
            break
        index += 1

    print("Dropping data column")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.drop_column('data')

    print("Renaming temp column to data")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='data',
                              existing_type=sa.BLOB(),
                              nullable=False
                              )


def downgrade_():
    print("Initializing")
    t_api_data = sa.Table(
        'api_data',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('data', sa.BLOB),
        sa.Column('temp', sa.JSON),
    )

    print("Adding temp column")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('temp', sa.JSON(), nullable=True))

    print("Populating temp column")
    connection = op.get_bind()
    index = 0
    while True:
        api_data = connection.execute(sa.select([t_api_data.c.id, t_api_data.c.data]).limit(1000).offset(index * 1000)).fetchall()
        for datum in api_data:
            decompressed_value = zlib.decompress(datum[1])
            decoded_value = decompressed_value.decode('UTF')
            json_value = json.loads(decoded_value)
            connection.execute(t_api_data.update().where(t_api_data.c.id == datum[0]).values(
                temp=json_value,
                ))
        if len(api_data):
            print(f"api data #{api_data[0][0]} - api data #{api_data[-1][0]}")
        if len(api_data) < 1000:
            break
        index += 1

    print("Dropping data column")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.drop_column('data')

    print("Renaming temp column to data")
    with op.batch_alter_table('api_data', schema=None) as batch_op:
        batch_op.alter_column('temp',
                              new_column_name='data',
                              existing_type=sa.JSON(),
                              nullable=False
                              )

