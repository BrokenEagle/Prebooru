# APP/LOGICAL/UTILITY.PY

# ## EXTERNAL IMPORTS
from flask import url_for


# ## FUNCTIONS

def unique_objects(objs):
    seen = set()
    output = []
    for obj in objs:
        if obj.id not in seen:
            seen.add(obj.id)
            output.append(obj)
    return output


def set_error(retdata, message):
    retdata['error'] = True
    retdata['message'] = message
    return retdata


def search_url_for(endpoint, base_args=None, **kwargs):
    """Construct search URL for any endpoint given a dict of search parameters"""
    def _recurse(current_key, arg_dict, url_args):
        for key in arg_dict:
            updated_key = current_key + '[' + key + ']'
            if type(arg_dict[key]) is dict:
                _recurse(updated_key, arg_dict[key], url_args)
            else:
                url_args[updated_key] = arg_dict[key]
    url_args = base_args if base_args is not None else {}
    _recurse('search', kwargs, url_args)
    return url_for(endpoint, **url_args)
