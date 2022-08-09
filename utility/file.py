# UTILITY/FILE.PY

# ## PYTHON IMPORTS
import os
import time
import json
import pathlib

# ## LOCAL IMPORTS
from .data import decode_unicode, decode_json, get_buffer_checksum


# ## FUNCTIONS

# #### Filename functions

def get_http_filename(webpath):
    start = webpath.rfind('/') + 1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath) + 1
    return webpath[start:end]


def get_file_extension(filepath):
    return filepath[filepath.rfind('.') + 1:]


def get_directory_path(filepath):
    return str(pathlib.Path(filepath).parent.resolve())


# #### File functions

def get_directory_listing(directory):
    try:
        return [filename for filename in next(os.walk(directory))[2]]
    except Exception as e:
        print("Error with directory listing:", directory, e)
        raise


def get_subdirectory_listing(directory):
    try:
        return [filename for filename in next(os.walk(directory))[1]]
    except Exception as e:
        print("Error with subdirectory listing:", directory, e)
        raise


def create_directory(filepath, isdir=False):
    """Create the directory path if it doesn't already exist"""
    directory = get_directory_path(filepath) if not isdir else filepath
    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_directory(filepath):
    if os.path.exists(filepath):
        os.rmdir(filepath)
        # Time to let the OS remove the directory to prevent OS errors
        time.sleep(0.01)


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


def copy_file(old_filepath, new_filepath, safe=False):
    if os.path.exists(old_filepath):
        buffer = put_get_raw(old_filepath, 'rb')
        put_get_raw(new_filepath, 'wb', buffer)
        if safe:
            checksum = get_buffer_checksum(buffer)
            buffer2 = put_get_raw(new_filepath, 'rb')
            checksum2 = get_buffer_checksum(buffer2)
            if checksum != checksum2:
                raise Exception(f"Error moving file from {old_filepath} to {new_filepath}")
        # Time to let the OS copy the file to prevent OS errors
        time.sleep(0.1)


def delete_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
        # Time to let the OS remove the file to prevent OS errors
        time.sleep(0.01)


def move_file(old_filepath, new_filepath, safe=False):
    copy_file(old_filepath, new_filepath, safe)
    delete_file(old_filepath)
