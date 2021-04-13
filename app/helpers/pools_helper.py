# APP\HELPERS\POOLS_HELPER.PY

# ## FUNCTIONS

def ItemIsOfType(item, type):
    return item.__table__.name == type


def ItemIsOfTypes(item, types):
    return any(map(lambda x: ItemIsOfType(item, x), types))


def MediaHeader(item):
    if ItemIsOfType(item, 'illust'):
        return item.type.title() + ':'
    if ItemIsOfType(item, 'post'):
        return ('Video' if item.file_ext in ['mp4'] else 'Image') + ':'
    return ""
