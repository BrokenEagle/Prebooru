# APP/LOGICAL/UTILITY.PY

# ## PYTHON IMPORTS
import logging
import os
import re
import json
import uuid
import hashlib
import datetime
import pathlib
import threading
import traceback


# ## CLASS

class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            try:
                self.function(*self.args, **self.kwargs)
            except Exception as e:
                print(repr(e))
                traceback.print_tb(e.__traceback__)


# ## FUNCTIONS

def safe_print(*args, **kwargs):
    temp = ''
    for arg in args:
        if type(arg) is str:
            temp += arg + ' '
        else:
            temp += repr(arg) + ' '
    temp.strip()
    print(temp.encode('ascii', 'backslashreplace').decode(), **kwargs)


def buffered_print(name, safe=False, sep=" ", end="\n"):
    header = name + " - " + uuid.uuid1().hex
    print("\n++++++++++ %s ++++++++++\n" % header, flush=True)
    print_func = safe_print if safe else print
    print_buffer = []

    def accumulator(*args):
        nonlocal print_buffer
        print_buffer += [*args, end]

    def printer():
        nonlocal print_buffer
        top_header = "========== %s ==========" % header
        print_buffer = ["\n", top_header, "\n"] + print_buffer
        print_buffer += [("=" * len(top_header)), "\n"]
        print_str = sep.join(map(str, print_buffer))
        print_func(print_str, flush=True)

    setattr(accumulator, 'print', printer)
    return accumulator


def error_print(error):
    print(repr(error))
    traceback.print_tb(error.__traceback__)


def process_utc_timestring(timestring):
    try:
        return datetime.datetime.fromisoformat(timestring.replace('Z', '+00:00')).replace(tzinfo=None)
    except Exception:
        logging.error('Failed parse datetime string')


def get_buffer_checksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()


def get_http_filename(webpath):
    start = webpath.rfind('/') + 1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath) + 1
    return webpath[start:end]


def get_file_extension(filepath):
    return filepath[filepath.rfind('.') + 1:]


def get_directory_path(filepath):
    return str(pathlib.Path(filepath).parent.resolve())


def decode_unicode(byte_string):
    try:
        decoded_string = byte_string.decode('utf')
    except Exception:
        print("Unable to decode data!")
        return
    return decoded_string


def decode_json(string):
    try:
        data = json.loads(string)
    except Exception:
        print("Invalid data!")
        return
    return data


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


def safe_get(input_dict, *keys):
    for key in keys:
        try:
            input_dict = input_dict[key]
        except (KeyError, TypeError):
            return None
    return input_dict


def is_truthy(string):
    truth_match = re.match(r'^(?:t(?:rue)?|y(?:es)?|1)$', string, re.IGNORECASE)
    return truth_match is not None


def is_falsey(string):
    false_match = re.match(r'^(?:f(?:alse)?|n(?:o)?|0)$', string, re.IGNORECASE)
    return false_match is not None


def eval_bool_string(string):
    if is_truthy(string):
        return True
    if is_falsey(string):
        return False


def static_vars(**kwargs):  # Unused
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def unique_objects(objs):
    seen = set()
    output = []
    for obj in objs:
        if obj.id not in seen:
            seen.add(obj.id)
            output.append(obj)
    return output


def set_precision(number, precision):
    placenum = 10**precision
    return (int(number * placenum)) / placenum


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


def merge_dicts(a, b):
    for key in b:
        if key in a and isinstance(a[key], dict) and isinstance(b[key], dict):
            merge_dicts(a[key], b[key])
        else:
            a[key] = b[key]
    return a


def set_error(retdata, message):
    retdata['error'] = True
    retdata['message'] = message
    return retdata


def fixup_crlf(text):
    return re.sub(r'(?<!\r)\n', '\r\n', text)


def get_environment_variable(key, default, parser=str):
    value = os.environ.get(key)
    return default if value is None else parser(value)
