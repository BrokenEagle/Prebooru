import os
from sqlalchemy import event, MetaData, Table, Column, String, select

from .. import DB, DATABASE_VERSION
from ..config import DB_PATH, JOBS_PATH, DEBUG_MODE

def validate_version():
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        t_alembic_version = Table('alembic_version', MetaData(), Column('version_num', String))
        engine = DB.get_engine(bind=None).engine
        connection = engine.connect()
        try:
            version = connection.execute(select([t_alembic_version.c.version_num])).first()[0]
        except Exception:
            print("\nError querying database for version number:", engine.url)
            exit(-1)
        if version != DATABASE_VERSION:
            print("\nMust upgrade the database:", version, '->', DATABASE_VERSION)
            exit(-1)
