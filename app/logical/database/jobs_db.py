# APP/LOGICAL/DATABASE/JOBS_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select, exists, Table, Column, MetaData, Unicode, Boolean, Float, JSON

# ## LOCAL IMPORTS
from ... import SCHEDULER_JOBSTORES


# ## GLOBAL VARIABLES

T_JOBS_INFO = SCHEDULER_JOBSTORES.jobs_t

T_JOBS_ENABLED = Table(
    'job_enabled',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('enabled', Boolean(), nullable=False),
)

T_JOBS_LOCK = Table(
    'job_locks',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('locked', Boolean(), nullable=False),
)

T_JOBS_MANUAL = Table(
    'job_manual',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('manual', Boolean(), nullable=False),
)


T_JOBS_TIME = Table(
    'job_times',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('time', Float(), nullable=False),
)

T_JOBS_STATUS = Table(
    'job_status',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('data', JSON(), nullable=False),
)


# ## FUNCTIONS

# ### Create

def create_job_tables():
    T_JOBS_INFO.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_ENABLED.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_LOCK.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_MANUAL.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_TIME.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_STATUS.create(SCHEDULER_JOBSTORES.engine, True)


def create_job_enabled(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_ENABLED.insert().values(id=id, enabled=True)
        conn.execute(statement)


def create_job_manual(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_MANUAL.insert().values(id=id, manual=False)
        conn.execute(statement)


def create_job_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.insert().values(id=id, locked=False)
        conn.execute(statement)


def create_job_timeval(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIME.insert().values(id=id, time=0.0)
        conn.execute(statement)


def create_job_status(id, data):
    if id is None:
        return
    print('create_job_status', id, data)
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_STATUS.insert().values(id=id, data=data)
        conn.execute(statement)


# #### Update

def update_job_next_run_time(id, timestamp):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_INFO.update().where(T_JOBS_INFO.c.id == id)\
                       .values(next_run_time=timestamp)
        conn.execute(statement)


def update_job_enabled_status(id, boolval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_ENABLED.update().where(T_JOBS_ENABLED.c.id == id)\
                          .values(enabled=boolval)
        conn.execute(statement)


def update_job_manual_status(id, boolval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_MANUAL.update().where(T_JOBS_MANUAL.c.id == id)\
                         .values(manual=boolval)
        conn.execute(statement)


def update_job_lock_status(id, boolval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_LOCK.update().where(T_JOBS_LOCK.c.id == id)\
                       .values(locked=boolval)
        conn.execute(statement)


def update_job_timeval(id, timestamp):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_TIME.update().where(T_JOBS_TIME.c.id == id)\
                       .values(time=timestamp)
        conn.execute(statement)


def update_job_status(id, data):
    if id is None:
        return
    print('update_job_status', id, data)
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement =\
            T_JOBS_STATUS.update().where(T_JOBS_STATUS.c.id == id)\
                         .values(data=data)
        conn.execute(statement)


# #### Delete

def delete_job(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_INFO.delete().where(T_JOBS_INFO.c.id == id)
        conn.execute(statement)


def delete_enabled(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_ENABLED.delete().where(T_JOBS_ENABLED.c.id == id)
        conn.execute(statement)


def delete_manual(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_MANUAL.delete().where(T_JOBS_MANUAL.c.id == id)
        conn.execute(statement)


def delete_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.delete().where(T_JOBS_LOCK.c.id == id)
        conn.execute(statement)


def delete_timeval(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIME.delete().where(T_JOBS_TIME.c.id == id)
        conn.execute(statement)


def delete_status(id):
    if id is None:
        return
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_STATUS.delete().where(T_JOBS_STATUS.c.id == id)
        conn.execute(statement)


# #### Query

def get_all_job_info():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_INFO.c.id, T_JOBS_INFO.c.next_run_time])
        timestamps = conn.execute(statement).fetchall()
        return {f[0]: datetime.datetime.fromtimestamp(f[1]) for f in timestamps}


def get_all_job_enabled():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_ENABLED.c.id, T_JOBS_ENABLED.c.enabled])
        enabled = conn.execute(statement).fetchall()
        return {f[0]: f[1] for f in enabled}


def get_all_job_manual():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_MANUAL.c.id, T_JOBS_MANUAL.c.manual])
        manual = conn.execute(statement).fetchall()
        return {f[0]: f[1] for f in manual}


def get_job_enabled_status(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_ENABLED.c.enabled]).where(T_JOBS_ENABLED.c.id == id)
        status = conn.execute(statement).fetchone()
        return status[0] if status is not None else None


def get_job_manual_status(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_MANUAL.c.manual]).where(T_JOBS_MANUAL.c.id == id)
        status = conn.execute(statement).fetchone()
        return status[0] if status is not None else None


def get_all_job_locks():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_LOCK.c.id, T_JOBS_LOCK.c.locked])
        locks = conn.execute(statement).fetchall()
        return {f[0]: f[1] for f in locks}


def get_job_lock_status(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_LOCK.c.locked]).where(T_JOBS_LOCK.c.id == id)
        status = conn.execute(statement).fetchone()
        return status[0] if status is not None else None


def is_any_job_locked():
    all_locks = get_all_job_locks()
    return any(lock for lock in all_locks.values())


def get_all_job_timevals():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_TIME.c.id, T_JOBS_TIME.c.time])
        vals = conn.execute(statement).fetchall()
        return {f[0]: f[1] for f in vals}


def get_job_timeval(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_TIME.c.time]).where(T_JOBS_TIME.c.id == id)
        val = conn.execute(statement).fetchone()
        return val[0] if val is not None else None


def check_job_status_exists(id):
    if id is None:
        return False
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = exists(T_JOBS_STATUS.c.id).where(T_JOBS_STATUS.c.id == id).select()
        return (conn.execute(statement).fetchone())[0]


def get_job_status_data(id):
    if id is None:
        return None
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_STATUS.c.data]).where(T_JOBS_STATUS.c.id == id)
        val = conn.execute(statement).fetchone()
        return val[0] if val is not None else None
