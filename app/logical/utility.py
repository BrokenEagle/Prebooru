# APP/LOGICAL/UTILITY.PY

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
