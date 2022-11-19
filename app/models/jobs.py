# APP/MODELS/JOBS.PY

# ## PYTHON IMPORTS
import datetime

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


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
    id = DB.Column(DB.String(255), primary_key=True)
    _next_run_time = DB.Column('next_run_time', DB.Float(), nullable=True)
    job_state = DB.Column(DB.BLOB(), nullable=False)

    # ## Properties

    @property
    def next_run_time(self):
        return datetime.datetime.fromtimestamp(self._next_run_time)

    # ## Private

    __tablename__ = 'apscheduler_jobs'


class JobEnable(JobBase):
    # ## Columns
    id = DB.Column(DB.String(255), primary_key=True)
    enabled = DB.Column(DB.Boolean(), nullable=False)


class JobManual(JobBase):
    # ## Columns
    id = DB.Column(DB.String(255), primary_key=True)
    manual = DB.Column(DB.Boolean(), nullable=False)


class JobLock(JobBase):
    # ## Columns
    id = DB.Column(DB.String(255), primary_key=True)
    locked = DB.Column(DB.Boolean(), nullable=False)


class JobTime(JobBase):
    # ## Columns
    id = DB.Column(DB.String(255), primary_key=True)
    time = DB.Column(DB.Float(), nullable=False)


class JobStatus(JobBase):
    # ## Columns
    id = DB.Column(DB.String(255), primary_key=True)
    data = DB.Column(DB.JSON(), nullable=False)
