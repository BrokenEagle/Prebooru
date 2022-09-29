# MIGRATIONS/COLUMNS.PY

# EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa

# PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

# #### Batch operations

def add_columns(table_name, add_column_commands):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for (column_name, column_type) in add_column_commands:
            batch_op.add_column(sa.Column(column_name, getattr(sa, column_type)(), nullable=True))


def drop_columns(table_name, column_names):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for column_name in column_names:
            batch_op.drop_column(column_name)


def alter_columns(table_name, alter_column_commands):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for (column_name, column_type, alter_args) in alter_column_commands:
            batch_op.alter_column(column_name, existing_type=getattr(sa, column_type)(), **alter_args)


# ## Single operations

def add_column(table_name, column_name, column_type):
    add_columns(table_name, [(column_name, column_type)])


def drop_column(table_name, column_name):
    drop_columns(table_name, [column_name])


def alter_column(table_name, column_name, column_type, alter_args):
    alter_columns(table_name, [(column_name, column_type, alter_args)])


def initialize_column(table_name, column_name, column_type, *extra_columns):
    columns = [sa.Column('id', sa.Integer), sa.Column(column_name, getattr(sa, column_type))]
    for (colname, coltype) in extra_columns:
        columns.append(sa.Column(colname, getattr(sa, coltype)))
    t = sa.Table(
        table_name,
        sa.MetaData(),
        *columns,
    )
    select = [t.c.id, getattr(t.c, column_name)]
    for (colname, _) in extra_columns:
        select.append(getattr(t.c, colname))
    connection = op.get_bind()
    index = 0
    while True:
        statement = sa.select(select).limit(1000).offset(index * 1000)
        data = connection.execute(statement).fetchall()
        for item in data:
            (id, value, *extra_values) = item
            def _update(**kwargs):
                connection.execute(t.update().where(t.c.id == id).values(**kwargs))
            yield id, value, _update, {extra_columns[i][0]: extra_values[i] for i in range(len(extra_values))}
        if len(data):
            print(f"{table_name} #{data[0][0]} - {table_name} #{data[-1][0]}")
        if len(data) < 1000:
            return
        index += 1


def transfer_column(table_name, from_column, to_column):
    from_name, from_type = from_column
    to_name, to_type = to_column
    t = sa.Table(
        table_name,
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column(from_name, getattr(sa, from_type)),
        sa.Column(to_name, getattr(sa, to_type)),
    )
    connection = op.get_bind()
    index = 0
    while True:
        statement = sa.select([t.c.id, getattr(t.c, from_name)])\
                      .limit(1000)\
                      .offset(index * 1000)
        data = connection.execute(statement).fetchall()
        for (id, value) in data:
            def _update(**kwargs):
                connection.execute(t.update().where(t.c.id == id).values(**kwargs))
            yield id, value, _update
        if len(data):
            print(f"{table_name} #{data[0][0]} - {table_name} #{data[-1][0]}")
        if len(data) < 1000:
            return
        index += 1
