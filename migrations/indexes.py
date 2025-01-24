# MIGRATIONS/INDEXES.PY

# EXTERNAL IMPORTS
import sqlalchemy as sa

# LOCAL IMPORTS
from . import batch_alter_table, get_inspector


# ## FUNCTIONS

# #### Batch operations

def create_indexes(table_name, add_index_commands, batch_kwargs=None):
    """
    Index command format:
    [0] index name (string)
    [1] column_names (array of strings)
    [2] unique (boolean)
    [3] keyword arguments (dict) [optional]
     - Example: {'sqlite_where': 'some_id IS NOT NULL'}
    """
    add_index_names = [comm[0] for comm in add_index_commands]
    indexes = get_inspector().get_indexes(table_name)
    remove_names = [index['name'] for index in indexes if index['name'] in add_index_names]
    if len(remove_names):
        drop_indexes(table_name, remove_names)

    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with batch_alter_table(table_name, **batch_kwargs) as batch_op:
        for (index_name, index_keys, *other) in add_index_commands:
            unique = other[0]  # Unique must always be specified explicitly
            kwargs = other[1] if len(other) > 1 else {}
            if 'sqlite_where' in kwargs and isinstance(kwargs['sqlite_where'], str):
                kwargs['sqlite_where'] = sa.text(kwargs['sqlite_where'])
            batch_op.create_index(batch_op.f(index_name), index_keys, unique=unique, **kwargs)


def drop_indexes(table_name, index_names, batch_kwargs=None):
    current_names = [index['name'] for index in get_inspector().get_indexes(table_name)]
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with batch_alter_table(table_name, **batch_kwargs) as batch_op:
        for index_name in index_names:
            if index_name not in current_names:
                continue
            batch_op.drop_index(batch_op.f(index_name))


# #### Single operations

def create_index(table_name, index_name, index_keys, unique, **kwargs):
    create_indexes(table_name, [(index_name, index_keys, unique, kwargs)])


def drop_index(table_name, index_name):
    drop_indexes(table_name, [index_name])


# #### Other functions

def make_index_wrapper(table_name, index_commands):
    """Alembic isn't able to properly restore partial indexes, so do it manually."""

    index_names = [arg[0] for arg in index_commands]

    def restore_index(func):
        def wrapper_func(*args, **kwargs):
            drop_indexes(table_name, index_names)
            func(*args, **kwargs)
            create_indexes(table_name, index_commands)

        return wrapper_func

    return restore_index
