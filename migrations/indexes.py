# MIGRATIONS/INDEXES.PY

# EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa

# PACKAGE IMPORTS
from config import NAMING_CONVENTION

# LOCAL IMPORTS
from . import get_inspector


# ## FUNCTIONS

# #### Batch operations

def create_indexes(table_name, add_index_commands, batch_kwargs=None):
    add_index_names = [comm[0] for comm in add_index_commands]
    indexes = get_inspector().get_indexes(table_name)
    remove_names = [index['name'] for index in indexes if index['name'] in add_index_names]
    if len(remove_names):
        drop_indexes(table_name, remove_names)

    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for (index_name, index_keys, *other) in add_index_commands:
            unique = other[0]  # Unique must always be specified explicitly
            kwargs = other[1] if len(other) > 1 else {}
            for key in kwargs:
                if key == 'sqlite_where' and isinstance(kwargs[key], str):
                    kwargs[key] = sa.text(kwargs[key])
            batch_op.create_index(batch_op.f(index_name), index_keys, unique=unique, **kwargs)


def drop_indexes(table_name, index_names, batch_kwargs=None):
    current_names = [index['name'] for index in get_inspector().get_indexes(table_name)]
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for index_name in index_names:
            if index_name not in current_names:
                continue
            batch_op.drop_index(batch_op.f(index_name))


# #### Single operations

def create_index(table_name, index_name, index_keys, unique, **kwargs):
    create_indexes(table_name, [(index_name, index_keys, unique, kwargs)])


def drop_index(table_name, index_name):
    drop_indexes(table_name, [index_name])
