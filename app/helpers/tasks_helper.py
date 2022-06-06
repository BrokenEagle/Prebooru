# APP/HELPERS/TASKS_HELPER.PY

import datetime

from utility.time import local_datetime_to_utc

# ## LOCAL IMPORTS
from .base_helper import format_expires


# ## FUNCTIONS

# #### Format functions

def format_next_run_time(job_id, timevals):
    timeval = local_datetime_to_utc(timevals[job_id]) if job_id in timevals else None
    return format_expires(timeval)
