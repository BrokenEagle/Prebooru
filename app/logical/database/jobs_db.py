# APP/LOGICAL/DATABASE/JOBS_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import inspect

# ## LOCAL IMPORTS
from ... import SESSION, DB
from ...models.jobs import JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus


# ## GLOBAL VARIABLES

JOB_ITEMS = {model._model_name(): model for model in [JobInfo, JobEnable, JobManual, JobLock, JobTime, JobStatus]}

JOB_ITEMS_CREATE = {
    'job_enable': lambda x, v: JobEnable(id=x, enabled=v),
    'job_manual': lambda x, v: JobManual(id=x, manual=v),
    'job_lock': lambda x, v: JobLock(id=x, locked=v),
    'job_time': lambda x, v: JobTime(id=x, time=v),
    'job_status': lambda x, v: JobStatus(id=x, data=v),
}

JOB_ITEMS_UPDATE = {
    'job_enable': lambda x, v: setattr(x, 'enabled', v),
    'job_manual': lambda x, v: setattr(x, 'manual', v),
    'job_lock': lambda x, v: setattr(x, 'locked', v),
    'job_time': lambda x, v: setattr(x, 'time', v),
}


# ## FUNCTIONS

# ### Create

def create_job_item(jobtype, id, val):
    item = JOB_ITEMS_CREATE[jobtype](id, val)
    SESSION.add(item)
    SESSION.flush()
    return item


# #### Update

def update_job_item(item, value):
    JOB_ITEMS_UPDATE[item.table_name](item, value)
    SESSION.flush()


def update_job_by_id(job_type, id, value_dict):
    JOB_ITEMS[job_type].query.filter_by(id=id).update(value_dict)
    SESSION.flush()


def update_job_status(id, data):
    if id is None:
        return
    job = JobStatus.find(id)
    job.data = data
    SESSION.commit()


# #### Delete

def delete_job_item(item):
    SESSION.delete(item)
    SESSION.flush()


# #### Query

def get_all_job_info():
    return {item.id: item.next_run_time for item in JobInfo.query.all()}


def get_all_job_items(job_type):
    return {item.id: item for item in JOB_ITEMS[job_type].query.all()}


def get_job_item(job_type, id):
    return JOB_ITEMS[job_type].find(id)


def is_any_job_locked():
    return JobLock.query.filter(JobLock.locked.is_(True)).first() is not None


def is_any_job_manual():
    return JobManual.query.filter(JobManual.locked.is_(True)).first() is not None


def get_job_status_data(id):
    if id is None:
        return None
    item = JobStatus.find(id)
    return item.data if item else None


# ## Misc

def create_or_update_job_status(id, status):
    item = JobStatus.find(id)
    if item is None:
        item = JobStatus(id=id)
        SESSION.add(item)
    item.data = status
    SESSION.flush()


def check_tables():
    required_names = ['alembic_version'] + [item._table_name() for item in JOB_ITEMS.values()]
    valid_names = ['sqlite_stat1'] + required_names
    with DB.get_engine(bind='jobs').connect() as conn:
        table_names = inspect(conn).get_table_names()
        for name in table_names:
            if name not in valid_names:
                conn.execute(f'DROP TABLE {name}')
    missing_tables = set(required_names).difference(table_names)
    if len(missing_tables) > 0:
        raise Exception(f"""Missing tables: {missing_tables}. Must run "prebooru.py init".""")
