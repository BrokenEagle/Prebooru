# UTILITY.PY

# ## PYTHON IMPORTS
import logging
import datetime

# ## LOCAL IMPORTS
from .data import set_precision


# ## FUNCTIONS


def process_utc_timestring(timestring):
    try:
        return datetime.datetime.fromisoformat(timestring.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        logging.error('Failed parse datetime string')


def get_current_time():
    t = datetime.datetime.utcnow()
    return t - datetime.timedelta(microseconds=t.microsecond)


def days_ago(days):  # Unused
    return get_current_time() - datetime.timedelta(days=days)


def days_from_now(days):
    return get_current_time() + datetime.timedelta(days=days)


def hours_from_now(hours):  # Unused
    return get_current_time() + datetime.timedelta(hours=hours)


def hours_ago(hours):  # Unused
    return get_current_time() - datetime.timedelta(hours=hours)


def minutes_from_now(minutes):  # Unused
    return get_current_time() + datetime.timedelta(minutes=minutes)


def minutes_ago(minutes):
    return get_current_time() - datetime.timedelta(minutes=minutes)


def seconds_from_now_local(seconds):
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds)


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


def add_dict_entry(indict, key, entry):
    indict[key] = indict[key] + [entry] if key in indict else [entry]
