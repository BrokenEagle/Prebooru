# UTILITY/TIME.PY

# ## PYTHON IMPORTS
import logging
import datetime

# ## LOCAL IMPORTS
from .data import set_precision


# ## FUNCTIONS

def local_datetime_utcoffset():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)


def local_datetime_to_utc(timeval):
    return timeval - local_datetime_utcoffset()


def process_utc_timestring(timestring):
    try:
        return datetime.datetime.fromisoformat(timestring.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        logging.error('Failed parse datetime string')


def datetime_from_epoch(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


def get_current_time():
    t = datetime.datetime.utcnow()
    return t - datetime.timedelta(microseconds=t.microsecond)


def add_days(timeval, days):
    return timeval + datetime.timedelta(days=days)


def add_hours(timeval, hours):
    return timeval + datetime.timedelta(hours=hours)


def days_ago(days):
    return add_days(get_current_time(), -days)


def days_from_now(days):
    return add_days(get_current_time(), days)


def hours_ago(hours):
    return add_hours(get_current_time(), -hours)


def hours_from_now(hours):
    return add_hours(get_current_time(), hours)


def minutes_from_now(minutes):  # Unused
    return get_current_time() + datetime.timedelta(minutes=minutes)


def minutes_ago(minutes):
    return get_current_time() - datetime.timedelta(minutes=minutes)


def seconds_from_now_local(seconds):
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds)


def get_date(timeval):
    return timeval.strftime("%Y-%m-%d")


def time_ago(timeval, precision=2):
    delta = get_current_time() - timeval
    precision_str = "%%.%df " % precision
    if delta.days == 0:
        if delta.seconds < 60:
            return "%d seconds ago" % delta.seconds
        if delta.seconds < 3600:
            return (precision_str + "minutes ago") % set_precision(delta.seconds / 60, precision)
        return (precision_str + "hours ago") % set_precision(delta.seconds / 3600, precision)
    days = delta.days + (delta.seconds / 86400)
    if days < 7:
        return (precision_str + "days ago") % set_precision(days, precision)
    if days < 30:
        return (precision_str + "weeks ago") % set_precision(days / 7, precision)
    if days < 365:
        return (precision_str + "months ago") % set_precision(days / 30, precision)
    return (precision_str + "years ago") % set_precision(days / 365, precision)


def time_from_now(timeval, precision=2):
    delta = timeval - get_current_time()
    if delta < datetime.timedelta(0):
        return "already past"
    precision_str = "%%.%df " % precision
    if delta.days == 0:
        if delta.seconds < 60:
            return "%d seconds from now" % delta.seconds
        if delta.seconds < 3600:
            return (precision_str + "minutes from now") % set_precision(delta.seconds / 60, precision)
        return (precision_str + "hours from now") % set_precision(delta.seconds / 3600, precision)
    days = delta.days + (delta.seconds / 86400)
    if days < 7:
        return (precision_str + "days from now") % set_precision(days, precision)
    if days < 30:
        return (precision_str + "weeks from now") % set_precision(days / 7, precision)
    if days < 365:
        return (precision_str + "months from now") % set_precision(days / 30, precision)
    return (precision_str + "years from now") % set_precision(days / 365, precision)
