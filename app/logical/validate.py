import os
import logging
import itertools
from sqlalchemy import event, MetaData, Table, Column, String, select

from .. import DB, DATABASE_VERSION
from ..config import DB_PATH, JOBS_PATH, DEBUG_MODE

def validate_version():
    t_alembic_version = Table('alembic_version', MetaData(), Column('version_num', String))
    engine = DB.get_engine(bind=None).engine
    connection = engine.connect()
    try:
        version = connection.execute(select([t_alembic_version.c.version_num])).first()[0]
    except Exception:
        logging.error("Error querying database for version number: %s", engine.url)
        exit(-1)
    if version != DATABASE_VERSION:
        logging.warning("Must upgrade the database: %s -> %s", version, DATABASE_VERSION)
        exit(-1)
    connection.close()


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
