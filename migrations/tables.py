# MIGRATIONS/TABLES.PY

# EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# LOCAL IMPORTS
from .constraints import drop_constraints, create_constraints


# ## FUNCTIONS

# ## Single operations

def create_table(name, col_config, ck_config=None, fk_config=None, pk_config=None, uq_config=None, with_rowid=True):
    columns = [sa.Column(v['name'], getattr(sa, v['type']), nullable=v['nullable']) for v in col_config]
    constraints = []
    if pk_config is not None and isinstance(pk_config, (tuple, list)):
        constraints += [sa.PrimaryKeyConstraint(*pk['columns'], name=op.f(pk['name'])) for pk in pk_config]
    if fk_config is not None and isinstance(fk_config, (tuple, list)):
        constraints += [sa.ForeignKeyConstraint(fk['columns'], fk['references'], name=op.f(fk['name']))
                        for fk in fk_config]
    if uq_config is not None and isinstance(pk_config, (tuple, list)):
        constraints += [sa.create_unique_constraint(op.f(uq['name']), uq['columns']) for uq in uq_config]
    if ck_config is not None and isinstance(ck_config, (tuple, list)):
        constraints += [sa.CheckConstraint(ck['value'], name=op.f(ck['name'])) for ck in ck_config]
    op.create_table(name, *columns, *constraints, sqlite_with_rowid=with_rowid)


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


def remove_temp_tables(table_names, add_precursor=True):
    temp_names = ['_alembic_tmp_' + name for name in table_names] if add_precursor else table_names
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    drop_tables = [name for name in temp_names if name in tables]
    for name in drop_tables:
        drop_table(name)
