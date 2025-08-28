# UTILITY/FILE.PY

# ## PYTHON IMPORTS
import os
import time
import json
import pathlib

# ## LOCAL IMPORTS
from .data import decode_unicode, decode_json, get_buffer_checksum, encode_json


# ## FUNCTIONS

# #### Filename functions

def get_http_filename(webpath):
    start = webpath.rfind('/') + 1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath) + 1
    return webpath[start:end]


def get_file_extension(filepath):
    return filepath[filepath.rfind('.') + 1:].split(':')[0]


def no_file_extension(filepath):
    return filepath[:filepath.rfind('.')]


def get_directory_path(filepath):
    return str(pathlib.Path(filepath).parent.resolve())


def filename_join(name, ext):
    return f'{name}.{ext}'


def network_path_join(*parts):
    return '/'.join(parts)


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


def clear_directory(filepath, recursive=False):
    listing = get_directory_listing(filepath)
    for name in listing:
        delete_file(os.path.join(filepath, name))
    delete_directory(filepath)


def copy_directory(from_filepath, to_filepath, safe=False):
    create_directory(to_filepath, isdir=True)
    listing = get_directory_listing(from_filepath)
    for name in listing:
        copy_file(os.path.join(from_filepath, name), os.path.join(to_filepath, name), safe=safe)


def put_get_raw(filepath, optype, data=None, ascii=False):
    if filepath != os.devnull:
        create_directory(filepath)
        if optype[0] == 'r' and not os.path.exists(filepath):
            return
    with open(filepath, optype) as file:
        if optype[0] in ['w', 'a']:
            return put_raw(file, data, ascii)
        elif optype[0] == 'r':
            return get_raw(file, data, ascii)


def put_raw(file, data, ascii):
    if ascii:
        data = data.encode('utf')
    return 0 if file.write(data) else -1


def get_raw(file, data, ascii):
    try:
        load = file.read()
    except Exception:
        print("File not found!")
        return
    return decode_unicode(load) if ascii else load


def put_get_json(filepath, optype, data=None, ascii=False):
    if optype[0] in ['w', 'a']:
        save_data = encode_json(data, ascii=ascii)
        # Try writing to null device first to avoid clobbering the files upon errors
        put_get_raw(os.devnull, optype, save_data, ascii)
        return put_get_raw(filepath, optype, save_data, ascii)
    if optype[0] == 'r':
        load = put_get_raw(filepath, optype, None, ascii)
        if load is not None:
            return decode_json(load)


def load_default(filepath, defaultvalue, binary=False, ascii=False):
    optype = 'rb' if binary else 'r'
    data = None
    if os.path.exists(filepath):
        data = put_get_json(filepath, optype, ascii=ascii)
    return defaultvalue if data is None else data


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
