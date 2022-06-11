# UTILITY/DATA.PY

# ## PYTHON IMPORTS
import re
import json
import math
import hashlib


# ## FUNCTIONS

# #### Data functions

def get_buffer_checksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()


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


def readable_bytes(bytes):
    i = math.floor(math.log(bytes) / math.log(1024))
    sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    return str(set_precision((bytes / math.pow(1024, i)), 2)) + ' ' + sizes[i]


# #### String functions

def display_case(string):
    return ' '.join(map(str.title, string.split('_')))


def kebab_case(string):
    string = re.sub(r'([a-z])([A-Z])', r'\g<1>-\g<2>', string)
    string = re.sub(r'[\s_]+', '-', string)
    return string.lower()


def snake_case(string):
    string = re.sub(r'([a-z])([A-Z])', r'\g<1>_\g<2>', string)
    string = re.sub(r'[\s-]+', '_', string)
    return string.lower()


def camel_case(string):
    def dashscore_repl(match):
        return match.group(1).upper()
    string = re.sub(r'[-_]([a-z])', dashscore_repl, string)
    return string[0].upper() + string[1:]


def fixup_crlf(text):
    return re.sub(r'(?<!\r)\n', '\r\n', text)


# #### Boolean functions

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


# #### Number functions

def set_precision(number, precision):
    placenum = 10**precision
    return (int(number * placenum)) / placenum


# #### Dict functions

def safe_get(input_dict, *keys):
    for key in keys:
        try:
            input_dict = input_dict[key]
        except (KeyError, TypeError):
            return None
    return input_dict


def safe_check(input_dict, valtype, *keys):
    value = safe_get(input_dict, *keys)
    return isinstance(value, valtype)


def add_dict_entry(indict, key, entry):
    indict[key] = indict[key] + [entry] if key in indict else [entry]


def merge_dicts(a, b):
    for key in b:
        if key in a and isinstance(a[key], dict) and isinstance(b[key], dict):
            merge_dicts(a[key], b[key])
        else:
            a[key] = b[key]
    return a
