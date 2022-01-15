# APP/LOGICAL/FILE.PY

# ##PYTHON IMPORTS
import os
import time
import json

# ###LOCAL IMPORTS
from .utility import get_directory_path, decode_unicode, decode_json


# ##FUNCTIONS

def get_directory_listing(directory):
    try:
        return [filename for filename in next(os.walk(directory))[2]]
    except Exception as e:
        print("Error with directory listing:", directory, e)
        raise


def create_directory(filepath):
    """Create the directory path if it doesn't already exist"""
    directory = get_directory_path(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)


def put_get_raw(filepath, optype, data=None, unicode=False):
    if filepath != os.devnull:
        create_directory(filepath)
        if optype[0] == 'r' and not os.path.exists(filepath):
            return
    with open(filepath, optype) as file:
        if optype[0] in ['w', 'a']:
            return put_raw(file, data, unicode)
        elif optype[0] == 'r':
            return get_raw(file, data, unicode)


def put_raw(file, data, unicode):
    if unicode:
        data = data.encode('utf')
    return 0 if file.write(data) else -1


def get_raw(file, data, unicode):
    try:
        load = file.read()
    except Exception:
        print("File not found!")
        return
    return decode_unicode(load) if unicode else load


def put_get_json(filepath, optype, data=None, unicode=False):
    if optype[0] in ['w', 'a']:
        save_data = json.dumps(data, ensure_ascii=unicode)
        # Try writing to null device first to avoid clobbering the files upon errors
        put_get_raw(os.devnull, optype, save_data, unicode)
        return put_get_raw(filepath, optype, save_data, unicode)
    if optype[0] == 'r':
        load = put_get_raw(filepath, optype, None, unicode)
        if load is not None:
            return decode_json(load)


def load_default(filepath, defaultvalue, binary=False, unicode=False):
    optype = 'rb' if binary else 'r'
    if os.path.exists(filepath):
        return put_get_json(filepath, optype, unicode=unicode)
    return defaultvalue


def delete_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        # Time to let the OS remove the file to prevent OS errors
        time.sleep(0.2)
