# APP/LOGICAL/FILE.PY

# ##PYTHON IMPORTS
import os
import json

# ###LOCAL IMPORTS
from .utility import GetDirectory, DecodeUnicode, DecodeJSON


# ##FUNCTIONS


def CreateDirectory(filepath):
    """Create the directory path if it doesn't already exist"""
    directory = GetDirectory(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)


def PutGetRaw(filepath, optype, data=None, unicode=False):
    if filepath != os.devnull:
        CreateDirectory(filepath)
        if optype[0] == 'r' and not os.path.exists(filepath):
            return
    with open(filepath, optype) as file:
        if optype[0] in ['w', 'a']:
            return PutRaw(file, data, unicode)
        elif optype[0] == 'r':
            return GetRaw(file, data, unicode)


def PutRaw(file, data, unicode):
    if unicode:
        data = data.encode('utf')
    return 0 if file.write(data) else -1


def GetRaw(file, data, unicode):
    try:
        load = file.read()
    except Exception:
        print("File not found!")
        return
    return DecodeUnicode(load) if unicode else load


def PutGetJSON(filepath, optype, data=None, unicode=False):
    if optype[0] in ['w', 'a']:
        save_data = json.dumps(data, ensure_ascii=unicode)
        # Try writing to null device first to avoid clobbering the files upon errors
        PutGetRaw(os.devnull, optype, save_data, unicode)
        return PutGetRaw(filepath, optype, save_data, unicode)
    if optype[0] == 'r':
        load = PutGetRaw(filepath, optype, None, unicode)
        if load is not None:
            return DecodeJSON(load)


def LoadDefault(filepath, defaultvalue, binary=False, unicode=False):
    optype = 'rb' if binary else 'r'
    if os.path.exists(filepath):
        return PutGetJSON(filepath, optype, unicode=unicode)
    return defaultvalue
