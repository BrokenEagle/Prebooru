# UTILITY/TIME.PY

# ## PYTHON IMPORTS
import time
import logging
import datetime

# ## EXTERNAL IMPORTS
import pytz

# ## LOCAL IMPORTS
from .data import set_precision


# ## FUNCTIONS

def local_timezone():
    return pytz.timezone(_local_pytz_name())


def local_datetime_utcoffset():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)


def local_datetime_to_utc(timeval):
    return timeval - local_datetime_utcoffset()


def process_utc_timestring(timestring):
    try:
        return _normalize_time(datetime.datetime.fromisoformat(timestring.replace('Z', '+00:00')).replace(tzinfo=None))
    except Exception:
        logging.error("Failed to parse datetime string: %s", timestring)


def datetime_from_epoch(timestamp):
    return _normalize_time(datetime.datetime.utcfromtimestamp(timestamp))


def datetime_to_epoch(timeval):
    return timeval.replace(tzinfo=datetime.timezone.utc).timestamp()


def get_current_time():
    return _normalize_time(datetime.datetime.utcnow())


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


def minutes_from_now(minutes):
    return get_current_time() + datetime.timedelta(minutes=minutes)


def minutes_ago(minutes):
    return get_current_time() - datetime.timedelta(minutes=minutes)


def seconds_from_now(seconds):
    return get_current_time() + datetime.timedelta(seconds=seconds)


def seconds_ago(seconds):
    return get_current_time() - datetime.timedelta(seconds=seconds)


def seconds_from_now_local(seconds):
    return _normalize_time(datetime.datetime.now(local_timezone()) + datetime.timedelta(seconds=seconds))


def get_date(timeval):
    return timeval.strftime("%Y-%m-%d")


def average_timedelta(timedeltas):
    return sum(timedeltas, datetime.timedelta(0)) / len(timedeltas)


def humanized_timedelta(delta, precision=2):
    precision_str = "%%.%df " % precision
    if delta.days == 0:
        if delta.seconds < 60:
            return "%d seconds" % delta.seconds
        if delta.seconds < 3600:
            return (precision_str + "minutes") % set_precision(delta.seconds / 60, precision)
        return (precision_str + "hours") % set_precision(delta.seconds / 3600, precision)
    days = delta.days + (delta.seconds / 86400)
    if days < 7:
        return (precision_str + "days") % set_precision(days, precision)
    if days < 30:
        return (precision_str + "weeks") % set_precision(days / 7, precision)
    if days < 365:
        return (precision_str + "months") % set_precision(days / 30, precision)
    return (precision_str + "years") % set_precision(days / 365, precision)


def time_ago(timeval, precision=2):
    delta = get_current_time() - timeval
    if delta < datetime.timedelta(0):
        return "not yet"
    return humanized_timedelta(delta, precision) + " ago"


def time_from_now(timeval, precision=2):
    delta = timeval - get_current_time()
    if delta < datetime.timedelta(0):
        return "already past"
    return humanized_timedelta(delta, precision) + " from now"


def get_timer(name):
    time_buffer = [time.perf_counter()]

    def accumulator(checkpoint):
        time_buffer.append(time.perf_counter())
        duration = time_buffer[-1] - time_buffer[-2]
        print(f"[{name}]-{checkpoint}: {duration}")

    return accumulator


def datetime_valid(dt_str):
    try:
        datetime.datetime.fromisoformat(dt_str)
    except Exception:
        return False
    return True


# ## Private

def _normalize_time(timeval):
    return timeval - datetime.timedelta(microseconds=timeval.microsecond)


def _local_pytz_name():
    offset = local_datetime_utcoffset()
    hours_ahead = int((offset.seconds // 3600) + (offset.days * 24))
    sign = "+" if hours_ahead <= 0 else "-"
    return 'Etc/GMT%s%d' % (sign, abs(hours_ahead))
