# APP/LOGICAL/DATABASE/JOBS_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select, Table, Column, MetaData, Unicode

# ## PACKAGE IMPORTS
from utility.time import get_current_time, process_utc_timestring

# ## LOCAL IMPORTS
from ... import DB, MAIN_PROCESS

# ## GLOBAL VARIABLES

T_SERVER_INFO = Table(
    'server_info',
    MetaData(),
    Column('field', Unicode(255), primary_key=True),
    Column('info', Unicode(255), nullable=False),
)

INITIALIZED = False


# ## FUNCTIONS

# ### Create

def create_table():
    T_SERVER_INFO.create(DB.engine, True)


def create_field(field, info):
    with DB.engine.begin() as conn:
        statement = T_SERVER_INFO.insert().values(field=field, info=info)
        conn.execute(statement)


# #### Update

def update_field(field, info):
    with DB.engine.begin() as conn:
        statement = T_SERVER_INFO.update().where(T_SERVER_INFO.c.field == field)\
                           .values(info=info)
        conn.execute(statement)


# #### Query

def query_field(field):
    with DB.engine.begin() as conn:
        statement = select([T_SERVER_INFO.c.info]).where(T_SERVER_INFO.c.field == field)
        val = conn.execute(statement).fetchone()
        return val[0] if val is not None else None


# #### Misc

def get_last_activity():
    last_activity = query_field('last_activity')
    return process_utc_timestring(last_activity) if last_activity is not None else None


def update_last_activity():
    global INITIALIZED
    current_time = datetime.datetime.isoformat(get_current_time())
    if MAIN_PROCESS and not INITIALIZED:
        INITIALIZED = True
        create_table()
        last_activity = query_field('last_activity')
        if last_activity is None:
            create_field('last_activity', current_time)
            return
    update_field('last_activity', current_time)
