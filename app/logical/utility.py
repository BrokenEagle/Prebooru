# APP/LOGICAL/UTILITY.PY

# ##PYTHON IMPORTS
import json
import iso8601
import hashlib

# ##FUNCTIONS


def ProcessTimestamp(timestring):
    """Get seconds from the Epoch for timestamps"""
    return round(iso8601.parse_date(timestring).timestamp())


def GetBufferChecksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()


def GetHTTPFilename(webpath):
    start = webpath.rfind('/') + 1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath) + 1
    return webpath[start:end]


def GetFileExtension(filepath):
    return filepath[filepath.rfind('.') + 1:]


def GetDirectory(filepath):
    return filepath[:filepath.rfind('\\') + 1]


def DecodeUnicode(byte_string):
    try:
        decoded_string = byte_string.decode('utf')
    except Exception:
        print("Unable to decode data!")
        return
    return decoded_string


def DecodeJSON(string):
    try:
        data = json.loads(string)
    except Exception:
        print("Invalid data!")
        return
    return data
