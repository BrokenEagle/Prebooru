# MIGRATIONS/INDEXES.PY

# EXTERNAL IMPORTS
import alembic.op as op

# PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

# #### Batch operations

def create_indexes(table_name, add_index_commands):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for (index_name, index_keys, unique) in add_index_commands:
            batch_op.create_index(batch_op.f(index_name), index_keys, unique=unique)


def drop_indexes(table_name, index_names):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for index_name in index_names:
            batch_op.drop_index(batch_op.f(index_name))


# #### Single operations

def create_index(table_name, index_name, index_keys, unique):
    create_indexes(table_name, [(index_name, index_keys, unique)])


def drop_index(table_name, index_name):
    drop_indexes(table_name, [index_name])
