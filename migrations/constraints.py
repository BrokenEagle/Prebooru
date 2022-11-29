# MIGRATIONS/CONSTRAINTS.PY

# PACKAGE IMPORTS
from migrations import batch_alter_table


# ## FUNCTIONS

# #### Batch operations

def create_constraints(table_name, add_constraint_commands, batch_op=None, batch_kwargs=None):
    def _process(batch_op, add_constraint_commands):
        for (constraint_name, constraint_type, args) in add_constraint_commands:
            switcher[constraint_type](batch_op, constraint_name, *args)

    switcher = {
        'primary': _create_primary_key_batch_op,
        'foreignkey': _create_foreign_key_batch_op,
        'unique': _create_unique_constraint_batch_op,
        'check': _create_check_constraint_batch_op,
    }
    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    if batch_op is None:
        with batch_alter_table(table_name, **batch_kwargs) as batch_op:
            _process(batch_op, add_constraint_commands)
    else:
        _process(batch_op, add_constraint_commands)


def drop_constraints(table_name, drop_constraint_commands, batch_op=None, batch_kwargs=None):
    def _process(batch_op, drop_constraint_commands):
        for (constraint_name, constraint_type) in drop_constraint_commands:
            batch_op.drop_constraint(batch_op.f(constraint_name), type_=constraint_type)

    batch_kwargs = batch_kwargs if isinstance(batch_kwargs, dict) else {}
    if batch_op is None:
        with batch_alter_table(table_name, **batch_kwargs) as batch_op:
            _process(batch_op, drop_constraint_commands)
    else:
        _process(batch_op, drop_constraint_commands)


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
