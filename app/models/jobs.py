# APP/MODELS/JOBS.PY

# ## PYTHON IMPORTS
import datetime

# ## LOCAL IMPORTS
from .base import JsonModel, text_column, real_column, boolean_column, blob_column, json_column


# ## CLASSES

class JobBase(JsonModel):
    # ## Properties

    @property
    def title(self):
        return self.id.replace('_', ' ').title()

    # ## Private

    __abstract__ = True

    __bind_key__ = 'jobs'

    __table_args__ = (
        {'sqlite_with_rowid': False},
    )


class JobInfo(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    next_run_time = real_column(nullable=True)
    job_state = blob_column(nullable=False)

    # ## Properties

    @property
    def next_run_time_datetime(self):
        return datetime.datetime.fromtimestamp(self.next_run_time)

    # ## Private

    __tablename__ = 'apscheduler_jobs'


class JobEnable(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    enabled = boolean_column(nullable=False)


class JobManual(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    manual = boolean_column(nullable=False)


class JobLock(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    locked = boolean_column(nullable=False)


class JobTime(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    time = real_column(nullable=False)


class JobStatus(JobBase):
    # ## Columns
    id = text_column(primary_key=True)
    data = json_column(nullable=False)
