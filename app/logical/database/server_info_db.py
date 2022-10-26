# APP/LOGICAL/DATABASE/SERVER_INFO_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## PACKAGE IMPORTS
from utility.time import get_current_time, process_utc_timestring, minutes_ago
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import ServerInfo
from .jobs_db import is_any_job_locked, is_any_job_manual


# ## GLOBAL VARIABLES

INITIALIZED = False

FIELD_UPDATERS = {
    'server_last_activity': lambda *args: datetime.datetime.isoformat(get_current_time()),
    'user_last_activity': lambda *args: datetime.datetime.isoformat(get_current_time()),
    'twitter_next_wait': lambda *args: str(get_current_time().timestamp() + (args[0] if len(args) else 0)),
    'pixiv_next_wait': lambda *args: str(get_current_time().timestamp() + (args[0] if len(args) else 0)),
    'subscriptions_ready': lambda *args: str(args[0] if len(args) else False),
}


# ## FUNCTIONS

# ## Decorators

def checkinit(func):

    def wrapper_func(*args, **kwargs):
        if INITIALIZED:
            return func(*args, **kwargs)

    return wrapper_func


# ### Create

def create_field(field, info):
    info = ServerInfo(field=field, info=info)
    SESSION.add(info)
    SESSION.flush()


# #### Update

def update_field(field, info):
    ServerInfo.query.filter_by(field=field).update({'info': info})
    SESSION.flush()


# #### Delete

def delete_field(field):
    ServerInfo.query.filter_by(field=field).delete()
    SESSION.flush()


# #### Query

def query_field(field):
    item = ServerInfo.find(field)
    return item.info if item is not None else None


def get_all_server_fields():
    items = ServerInfo.query.with_entities(ServerInfo.field).all()
    return [item[0] for item in items]


# #### Misc

@checkinit
def get_last_activity(type):
    field = type + '_last_activity'
    last_activity = query_field(field)
    return process_utc_timestring(last_activity) if last_activity is not None else None


@checkinit
def update_last_activity(type):
    field = type + '_last_activity'
    value = FIELD_UPDATERS[field]()
    update_field(field, value)


def server_is_busy():
    return any((
        get_last_activity('user') > minutes_ago(15),
        (get_last_activity('server') > minutes_ago(5)) and (is_any_job_locked() or is_any_job_manual()),
    ))


@checkinit
def get_next_wait(kind):
    field = kind + '_next_wait'
    next_wait = query_field(field)
    return float(next_wait) if next_wait is not None else None


@checkinit
def update_next_wait(kind, duration):
    field = kind + '_next_wait'
    value = FIELD_UPDATERS[field](duration)
    update_field(field, value)


@checkinit
def get_subscriptions_ready():
    ready = query_field('subscriptions_ready')
    return eval_bool_string(ready) if ready is not None else None


@checkinit
def update_subscriptions_ready(ready):
    value = FIELD_UPDATERS['subscriptions_ready'](ready)
    update_field('subscriptions_ready', value)


# #### Initialization

def initialize_server_fields():
    global INITIALIZED
    if INITIALIZED:
        return
    current_fields = get_all_server_fields()
    all_fields = list(FIELD_UPDATERS.keys())
    for field in current_fields:
        if field not in all_fields:
            delete_field(field)
    for field in all_fields:
        value = FIELD_UPDATERS[field]()
        if field not in current_fields:
            create_field(field, value)
        else:
            update_field(field, value)
    SESSION.commit()
    INITIALIZED = True
