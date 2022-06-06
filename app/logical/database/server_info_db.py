# APP/LOGICAL/DATABASE/SERVER_INFO_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select, Table, Column, MetaData, Unicode

# ## PACKAGE IMPORTS
from utility.time import get_current_time, process_utc_timestring, minutes_ago

# ## LOCAL IMPORTS
from ... import DB
from .jobs_db import is_any_job_locked


# ## GLOBAL VARIABLES

INITIALIZED = False

T_SERVER_INFO = Table(
    'server_info',
    MetaData(),
    Column('field', Unicode(255), primary_key=True),
    Column('info', Unicode(255), nullable=False),
)

INFO_FIELDS = ['server_last_activity', 'user_last_activity', 'twitter_next_wait', 'pixiv_next_wait']

FIELD_UPDATERS = {
    'server_last_activity': lambda *args: datetime.datetime.isoformat(get_current_time()),
    'user_last_activity': lambda *args: datetime.datetime.isoformat(get_current_time()),
    'twitter_next_wait': lambda *args: str(get_current_time().timestamp() + (args[0] if len(args) else 0)),
    'pixiv_next_wait': lambda *args: str(get_current_time().timestamp() + (args[0] if len(args) else 0)),
}


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


# #### Delete

def delete_field(field):
    with DB.engine.begin() as conn:
        statement = T_SERVER_INFO.delete().where(T_SERVER_INFO.c.field == field)
        conn.execute(statement)


# #### Query

def query_field(field):
    with DB.engine.begin() as conn:
        statement = select([T_SERVER_INFO.c.info]).where(T_SERVER_INFO.c.field == field)
        val = conn.execute(statement).fetchone()
        return val[0] if val is not None else None


def get_all_server_fields():
    with DB.engine.begin() as conn:
        statement = select([T_SERVER_INFO.c.field])
        fields = conn.execute(statement).fetchall()
        return [field[0] for field in fields]


# #### Misc

def get_last_activity(type):
    if not INITIALIZED:
        return None
    field = type + '_last_activity'
    last_activity = query_field(field)
    return process_utc_timestring(last_activity) if last_activity is not None else None


def update_last_activity(type):
    if not INITIALIZED:
        return
    field = type + '_last_activity'
    value = FIELD_UPDATERS[field]()
    update_field(field, value)


def server_is_busy():
    return (get_last_activity('user') > minutes_ago(15)) or ((get_last_activity('server') > minutes_ago(5)) and is_any_job_locked())


def get_next_wait(kind):
    if not INITIALIZED:
        return None
    field = kind + '_next_wait'
    next_wait = query_field(field)
    return float(next_wait) if next_wait is not None else None


def update_next_wait(kind, duration):
    if not INITIALIZED:
        return
    field = kind + '_next_wait'
    value = FIELD_UPDATERS[field](duration)
    update_field(field, value)


# #### Private

def initialize_server_fields():
    global INITIALIZED
    if INITIALIZED:
        return
    create_table()
    current_fields = get_all_server_fields()
    for field in current_fields:
        if field not in INFO_FIELDS:
            delete_field(field)
    for field in INFO_FIELDS:
        value = FIELD_UPDATERS[field]()
        if field not in current_fields:
            create_field(field, value)
    INITIALIZED = True
