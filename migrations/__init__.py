# MIGRATIONS/__INIT__.PY

"""Module for code used to help with migrations."""

# ## EXTERNAL IMPORTS
import alembic.op as op
import sqlalchemy as sa


# ## FUNCTIONS

def get_inspector():
    conn = op.get_bind()
    return sa.inspect(conn)
