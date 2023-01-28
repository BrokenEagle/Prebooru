# APP/LOGICAL/VALIDATE.PY

# ## PYTHON IMPORTS
import os
import sys
import sqlite3
import logging
import itertools

# ## EXTERNAL IMPORTS
from alembic import script, config
from alembic.runtime import migration

# ## PACKAGE IMPORTS
from utility.uprint import print_info, print_warning, print_error


# ## GLOBAL_VARIABLES

ALEMBIC_SCRIPT_FILE = os.path.join(os.getcwd(), 'migrations', 'alembic.ini')

ALEMBIC_VERSION_TABLE = """
CREATE TABLE alembic_version_temp (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY(version_num)
) WITHOUT ROWID
"""


# ## FUNCTIONS

def validate_python():
    if sys.version_info == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 7):
        print_error("Python version must be at least 3.7 to run this application.")
        exit(-1)


def validate_version(conn):
    database_head = migration.MigrationContext.configure(conn).get_current_heads()[0]
    directory_head = script.ScriptDirectory.from_config(config.Config(ALEMBIC_SCRIPT_FILE)).get_heads()[0]
    if database_head != directory_head:
        logging.warning("Must upgrade the database: (current) %s -> (head) %s", database_head, directory_head)
        exit(-1)


def validate_integrity(conn):
    check = conn.execute("PRAGMA quick_check").fetchone()
    if check != ('ok',):
        logging.error("The database has malformed data on disk")
        table_names = conn.execute("SELECT name FROM 'main'.sqlite_master WHERE type='table';").fetchall()
        table_names = sorted(itertools.chain(*table_names))
        for name in table_names:
            check = conn.execute("PRAGMA quick_check(%s)" % name).fetchone()
            status = 'OK' if check == ('ok',) else 'BAD'
            print("    %s: %s" % (name, status))
        exit(-1)
    else:
        print_info("\nDatabase: OK\n")


def validate_foreign_keys(conn):
    from ..models import TABLES
    table_fkeys = {}
    errors = conn.execute("PRAGMA foreign_key_check").fetchall()
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
            record = model.query.filter(model.rowid == rowid).fetchone()
            print(record)
            if name in table_fkeys:
                fkeys = table_fkeys[name]
            else:
                fkeys = table_fkeys[name] = conn.execute(f"PRAGMA foreign_key_list({name})").fetchall()
            error_fkey = next(fkey for fkey in fkeys if fkey[0] == fkid)
            print("FKEY", error_fkey)
            print('--------------------INVESTIGATE-------------------\n')
        exit(-1)
    else:
        print_info("\nForeign Keys: OK\n")


def validate_alembic_table(conn):
    if sqlite3.sqlite_version_info[1] < 37:
        print_warning("Unable to check alembic_version table. Upgrade SQLite to version 3.37.0 or greater.")
        return
    table_info = conn.execute("PRAGMA table_list(alembic_version)").fetchone()
    if table_info[4] == 1:
        print_info("\nAlembic Version table: OK\n")
        return
    conn.execute(ALEMBIC_VERSION_TABLE.strip())
    conn.execute("INSERT INTO alembic_version_temp SELECT * FROM alembic_version")
    conn.execute("DROP TABLE alembic_version")
    conn.execute("ALTER TABLE alembic_version_temp RENAME TO alembic_version")
    conn.execute("COMMIT")
    print_warning("\nAlembic Version table: MODIFIED\n")
