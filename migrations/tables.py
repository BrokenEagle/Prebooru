# MIGRATIONS/TABLES.PY

# EXTERNAL IMPORTS
import alembic.op as op
from sqlalchemy.engine.reflection import Inspector

# LOCAL IMPORTS
from .constraints import drop_constraints, create_constraints


# ## FUNCTIONS

# ## Single operations

def drop_table(table_name):
    op.drop_table(table_name)


def rename_table(old_name, new_name, old_config, new_config):
    print("Dropping constraints")
    drop_commands = [(k, v['type']) for (k, v) in old_config.items()]
    drop_constraints(old_name, drop_commands)

    print(f"Renaming table from {old_name} to {new_name}")
    op.rename_table(old_name, new_name)

    print("Creating constraints")
    create_commands = [(k, v['type'], v['args']) for (k, v) in new_config.items()]
    create_constraints(new_name, create_commands)


def remove_temp_tables(table_names):
    temp_names = ['_alembic_tmp_' + name for name in table_names]
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    drop_tables = [name for name in temp_names if name in tables]
    for name in drop_tables:
        drop_table(name)
