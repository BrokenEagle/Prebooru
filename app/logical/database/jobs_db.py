# APP/LOGICAL/DATABASE/JOBS_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select, Table, Column, MetaData, Unicode, Boolean, Float

# ## LOCAL IMPORTS
from ... import SCHEDULER_JOBSTORES


# ## GLOBAL VARIABLES

T_JOBS_INFO = SCHEDULER_JOBSTORES.jobs_t

T_JOBS_LOCK = Table(
    'job_locks',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('locked', Boolean(), nullable=False),
)

T_JOBS_TIME = Table(
    'job_times',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('time', Float(), nullable=False),
)


# ## FUNCTIONS

# ### Create

def create_job_tables():
    T_JOBS_LOCK.create(SCHEDULER_JOBSTORES.engine, True)
    T_JOBS_TIME.create(SCHEDULER_JOBSTORES.engine, True)


def create_job_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.insert().values(id=id, locked=False)
        conn.execute(statement)


def create_job_timeval(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIME.insert().values(id=id, time=0.0)
        conn.execute(statement)


# #### Update

def update_job_next_run_time(id, timestamp):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_INFO.update().where(T_JOBS_INFO.c.id == id)\
                           .values(next_run_time=timestamp)
        conn.execute(statement)


def update_job_lock_status(id, boolval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.update().where(T_JOBS_LOCK.c.id == id)\
                           .values(locked=boolval)
        conn.execute(statement)


def update_job_timeval(id, timestamp):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIME.update().where(T_JOBS_TIME.c.id == id)\
                           .values(time=timestamp)
        conn.execute(statement)


# #### Delete

def delete_job(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_INFO.delete().where(T_JOBS_INFO.c.id == id)
        conn.execute(statement)


def delete_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.delete().where(T_JOBS_LOCK.c.id == id)
        conn.execute(statement)


def delete_timeval(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIME.delete().where(T_JOBS_TIME.c.id == id)
        conn.execute(statement)


# #### Query

def get_all_job_info():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_INFO.c.id, T_JOBS_INFO.c.next_run_time])
        timestamps = conn.execute(statement).fetchall()
        return {f[0]: datetime.datetime.fromtimestamp(f[1]) for f in timestamps}


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
