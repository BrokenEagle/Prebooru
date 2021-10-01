# APP/LOGICAL/DATABASE/JOBS_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select, Table, Column, MetaData, Unicode, Boolean

# ## LOCAL IMPORTS
from ... import SCHEDULER_JOBSTORES


# ## GLOBAL VARIABLES

T_JOBS_TIMES = SCHEDULER_JOBSTORES.jobs_t

T_JOBS_LOCK = Table(
    'job_locks',
    MetaData(),
    Column('id', Unicode(255), primary_key=True),
    Column('locked', Boolean(), nullable=False),
)


# ## FUNCTIONS

# ### Create

def create_locks_on_startup():
    T_JOBS_LOCK.create(SCHEDULER_JOBSTORES.engine, True)


def create_job_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.insert().values(id=id, locked=False)
        conn.execute(statement)


# #### Update

def update_job_next_run_time(id, timeval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIMES.update().where(T_JOBS_TIMES.c.id == id)\
                           .values(next_run_time=timeval.timestamp())
        conn.execute(statement)


def update_job_lock_status(id, boolval):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.update().where(T_JOBS_LOCK.c.id == id)\
                           .values(locked=boolval)
        conn.execute(statement)


# #### Delete

def delete_job(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_TIMES.delete().where(T_JOBS_TIMES.c.id == id)
        conn.execute(statement)


def delete_lock(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = T_JOBS_LOCK.delete().where(T_JOBS_LOCK.c.id == id)
        conn.execute(statement)


# #### Query

def get_job_times():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_TIMES.c.id, T_JOBS_TIMES.c.next_run_time])
        timestamps = conn.execute(statement).fetchall()
        return {f[0]: datetime.datetime.fromtimestamp(f[1]) for f in timestamps}


def get_job_locks():
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_LOCK.c.id, T_JOBS_LOCK.c.locked])
        locks = conn.execute(statement).fetchall()
        return {f[0]: f[1] for f in locks}


def get_job_lock_status(id):
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([T_JOBS_LOCK.c.locked]).where(T_JOBS_LOCK.c.id == id)
        status = conn.execute(statement).fetchone()
        return status[0] if status is not None else None
