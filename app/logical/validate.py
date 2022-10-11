# APP/LOGICAL/VALIDATE.PY

# ## PYTHON IMPORTS
import os
import sys
import logging
import itertools

# ## EXTERNAL IMPORTS
from alembic import script, config
from alembic.runtime import migration

# ## PACKAGE IMPORTS
from utility.print import print_info, print_warning, print_error


# ## GLOBAL_VARIABLES

ALEMBIC_SCRIPT_FILE = os.path.join(os.getcwd(), 'migrations', 'alembic.ini')


# ## FUNCTIONS

def validate_python():
    if sys.version_info == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 7):
        print_error("Python version must be at least 3.7 to run this application.")
        exit(-1)


def validate_version():
    from .. import DB
    with DB.engine.begin() as conn:
        database_head = migration.MigrationContext.configure(conn).get_current_heads()[0]
    directory_head = script.ScriptDirectory.from_config(config.Config(ALEMBIC_SCRIPT_FILE)).get_heads()[0]
    if database_head != directory_head:
        logging.warning("Must upgrade the database: (current) %s -> (head) %s", database_head, directory_head)
        exit(-1)


def validate_integrity():
    from .. import DB
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
        print_info("\nDatabase: OK\n")


def validate_foreign_keys():
    from .. import DB, SESSION
    from ..models import TABLES
    table_fkeys = {}
    engine = DB.get_engine(bind=None).engine
    connection = engine.connect()
    errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if len(errors) > 0:
        logging.error("The database has orphaned foreign keys")
        print("\n    %-40s %-10s %-40s %s" % ("Table", "Row ID", "Parent", "FKey ID"))
        for (i, error) in enumerate(errors):
            print_warning("%02d. %-40s %-10d %-40s %d" % ((i + 1,) + tuple(error)))
        print('\n')
        for (i, error) in enumerate(errors):
            print_warning(f"Error record #{i + 1}")
            name, rowid, parent, fkid = error
            model = TABLES[name]
            record = model.query.filter(model.rowid == rowid).first()
            print(record)
            if name in table_fkeys:
                fkeys = table_fkeys[name]
            else:
                fkeys = table_fkeys[name] = connection.execute(f"PRAGMA foreign_key_list({name})").fetchall()
            error_fkey = next(fkey for fkey in fkeys if fkey[0] == fkid)
            print("FKEY", error_fkey)
            print('--------------------INVESTIGATE-------------------\n')
        exit(-1)
    else:
        print_info("\nForeign Keys: OK\n")
