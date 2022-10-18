# MIGRATIONS/CONSTRAINTS.PY

# EXTERNAL IMPORTS
import alembic.op as op

# PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

# #### Batch operations

def create_constraints(table_name, add_constraint_commands, batch_kwargs=None):
    switcher = {
        'primary': _create_primary_key_batch_op,
        'foreignkey': _create_foreign_key_batch_op,
        'unique': _create_unique_constraint_batch_op,
        'check': _create_check_constraint_batch_op,
    }
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for (constraint_name, constraint_type, *args) in add_constraint_commands:
            switcher[constraint_type](batch_op, constraint_name, *args)


def drop_constraints(table_name, drop_constraint_commands, batch_kwargs=None):
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    with op.batch_alter_table(table_name, naming_convention=NAMING_CONVENTION, **batch_kwargs) as batch_op:
        for (constraint_name, constraint_type) in drop_constraint_commands:
            batch_op.drop_constraint(batch_op.f(constraint_name), type_=constraint_type)


# #### Single operations

def create_constraint(table_name, constraint_name, constraint_type, args, **kwargs):
    create_constraints(table_name, [(constraint_name, constraint_type, args)], **kwargs)


def drop_constraint(table_name, constraint_name, constraint_type, **kwargs):
    drop_constraints(table_name, [(constraint_name, constraint_type)], **kwargs)


# #### Private functions

def _create_primary_key_batch_op(batch_op, constraint_name, keys):
    batch_op.create_primary_key(batch_op.f(constraint_name), keys)


def _create_foreign_key_batch_op(batch_op, constraint_name, source_table, fk_column_names, source_column_names):
    batch_op.create_foreign_key(batch_op.f(constraint_name), source_table, fk_column_names, source_column_names)


def _create_unique_constraint_batch_op(batch_op, constraint_name, keys):
    batch_op.create_unique_constraint(batch_op.f(constraint_name), keys)


def _create_check_constraint_batch_op(batch_op, constraint_name, constraint_value):
    batch_op.create_check_constraint(constraint_name, constraint_value)
