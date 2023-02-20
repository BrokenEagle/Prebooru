# MIGRATIONS/__INIT__.PY

"""Module for code used to help with migrations."""

# ## EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from config import NAMING_CONVENTION


# ## FUNCTIONS

def get_inspector():
    conn = op.get_bind()
    return sa.inspect(conn)


def batch_alter_table(table_name, naming=False, **batch_kwargs):
    naming_convention = NAMING_CONVENTION if naming else None
    return op.batch_alter_table(table_name, naming_convention=naming_convention, **batch_kwargs)
