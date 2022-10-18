# MIGRATIONS/COLUMNS.PY

# EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa

# PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

# #### Batch operations

def add_columns(table_name, add_column_commands, batch_kwargs=None):
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for (column_name, column_type) in add_column_commands:
            batch_op.add_column(sa.Column(column_name, getattr(sa, column_type)(), nullable=True))


def drop_columns(table_name, column_names, batch_kwargs=None):
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for column_name in column_names:
            batch_op.drop_column(column_name)


def alter_columns(table_name, alter_column_commands, batch_kwargs=None):
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for (column_name, column_type, alter_args) in alter_column_commands:
            batch_op.alter_column(column_name, existing_type=getattr(sa, column_type)(), **alter_args)


def transfer_columns(table_name, from_config, to_config):
    from_names = [k for k in from_config]
    columns = [sa.Column(k, getattr(sa, v)) for (k, v) in from_config.items()] +\
              [sa.Column(k, getattr(sa, v)) for (k, v) in to_config.items()]
    t = sa.Table(table_name, sa.MetaData(), sa.Column('id', sa.Integer), *columns)
    all_names = ['id'] + from_names
    base_statement = sa.select([t.c.id] + [getattr(t.c, name) for name in from_names]).limit(1000)
    connection = op.get_bind()
    index = 0
    while True:
        statement = base_statement.offset(index * 1000)
        page_data = connection.execute(statement).fetchall()
        if len(page_data):
            print(f"{table_name} #{page_data[0][0]} - {table_name} #{page_data[-1][0]}")
        for item in page_data:
            mapped_data = {all_names[i]: item[i] for i in range(len(item))}

            def _update(**kwargs):
                connection.execute(t.update().where(t.c.id == mapped_data['id']).values(**kwargs))

            yield id, mapped_data, _update
        if len(page_data) < 1000:
            return
        index += 1


# ## Single operations

def add_column(table_name, column_name, column_type, **kwargs):
    add_columns(table_name, [(column_name, column_type)], **kwargs)


def drop_column(table_name, column_name, **kwargs):
    drop_columns(table_name, [column_name], **kwargs)


def alter_column(table_name, column_name, column_type, alter_args, **kwargs):
    alter_columns(table_name, [(column_name, column_type, alter_args)], **kwargs)


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


# ## Combined operations

def change_column_type(table_name, column_name, from_column_type, to_column_type, base_column_type, nullable, **kwargs):
    print("Adding temp column")
    add_column(table_name, 'temp', to_column_type)

    print("Populating temp column")
    for (_id, value, update) in transfer_column(table_name, (column_name, from_column_type), ('temp', to_column_type)):
        yield value, update

    print(f"Dropping {column_name} column")
    drop_column(table_name, column_name)

    print(f"Renaming temp column to {column_name}")
    alter_column(table_name, 'temp', base_column_type, {'new_column_name': column_name, 'nullable': nullable})


def change_columns_type(table_name, columns_config):
    print("Adding temp columns")
    add_commands = [(k + '_temp', v['to']) for (k, v) in columns_config.items()]
    add_columns(table_name, add_commands)

    print("Populating temp columns")
    from_config = {k: v['from'] for (k, v) in columns_config.items()}
    to_config = {k + '_temp': v['to'] for (k, v) in columns_config.items()}
    for (_id, mapped_data, update) in transfer_columns(table_name, from_config, to_config):
        yield mapped_data, update

    print("Dropping old columns")
    drop_columns(table_name, [k for k in columns_config])

    print("Renaming temp columns and setting nullable")
    alter_commands = [(k + '_temp', v['base'], {'new_column_name': k, 'nullable': v['nullable']})
                      for (k, v) in columns_config.items()]
    alter_columns(table_name, alter_commands)
