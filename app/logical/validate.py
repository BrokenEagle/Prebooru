# APP/LOGICAL/VALIDATE.PY

# ## PYTHON IMPORTS
import os
import logging
import itertools

# ## EXTERNAL IMPORTS
from alembic import script, config
from alembic.runtime import migration
from sqlalchemy import MetaData, Table, Column, String, select

# ## LOCAL IMPORTS
from .. import DB

# ## GLOBAL_VARIABLES

ALEMBIC_SCRIPT_FILE = os.path.join(os.getcwd(), 'migrations', 'alembic.ini')


# ## FUNCTIONS

def validate_version():
    with DB.engine.begin() as conn:
        database_head = migration.MigrationContext.configure(conn).get_current_heads()[0]
    directory_head = script.ScriptDirectory.from_config(config.Config(ALEMBIC_SCRIPT_FILE)).get_heads()[0]
    if database_head != directory_head:
        logging.warning("Must upgrade the database: (current) %s -> (head) %s", database_head, directory_head)
        exit(-1)


def validate_integrity():
    engine = DB.get_engine(bind=None).engine
    connection = engine.connect()
    check = connection.execute("PRAGMA quick_check").first()
    if check != ('ok',):
        logging.error("The database has malformed data on disk")
        table_names = connection.execute("SELECT name FROM 'main'.sqlite_master WHERE type='table';").fetchall()
        table_names = sorted(itertools.chain(*table_names))
        for name in table_names:
            check = connection.execute("PRAGMA quick_check(%s)" % name).first()
            status = 'OK' if check == ('ok',) else 'BAD'
            print("    %s: %s" % (name, status))
        exit(-1)
    else:
        print("\nDatabase: OK")
