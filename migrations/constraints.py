# MIGRATIONS/CONSTRAINTS.PY

# EXTERNAL IMPORTS
import alembic.op as op

# PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

# #### Batch operations

def create_constraints(table_name, add_constraint_commands):
    switcher = {
        'primary': _create_primary_key_batch_op,
        'foreignkey': _create_foreign_key_batch_op,
        'unique': _create_unique_constraint_batch_op,
        'check': _create_check_constraint_batch_op,
    }
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for (constraint_name, constraint_type, *args) in add_constraint_commands:
            switcher[constraint_type](batch_op, constraint_name, *args)


def drop_constraints(table_name, drop_constraint_commands):
    with op.batch_alter_table(table_name, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        for (constraint_name, constraint_type) in drop_constraint_commands:
            batch_op.drop_constraint(batch_op.f(constraint_name), type_=constraint_type)


# #### Single operations

def create_constraint(table_name, constraint_name, constraint_type, args):
    create_constraints(table_name, [(constraint_name, constraint_type, args)])


def drop_constraint(table_name, constraint_name, constraint_type):
    drop_constraints(table_name, [(constraint_name, constraint_type)])


# #### Private functions

def _create_primary_key_batch_op(batch_op, constraint_name, keys):
    batch_op.create_primary_key(batch_op.f(constraint_name), keys)


def _create_foreign_key_batch_op(batch_op, constraint_name, source_table, fk_column_names, source_column_names):
    batch_op.create_foreign_key(batch_op.f(constraint_name), source_table, fk_column_names, source_column_names)


def _create_unique_constraint_batch_op(batch_op, constraint_name, keys):
    batch_op.create_unique_constraint(batch_op.f(constraint_name), keys)


def _create_check_constraint_batch_op(batch_op, constraint_name, constraint_value):
    batch_op.create_check_constraint(constraint_name, constraint_value)
