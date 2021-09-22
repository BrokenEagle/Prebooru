# APP\HELPERS\POOLS_HELPER.PY

# ## FUNCTIONS

def item_is_of_type(item, type):
    return item.__table__.name == type


def item_is_of_types(item, types):
    return any(map(lambda x: item_is_of_type(item, x), types))


def media_header(item):
    if item_is_of_type(item, 'illust'):
        return item.type.title() + ':'
    if item_is_of_type(item, 'post'):
        return ('Video' if item.file_ext in ['mp4'] else 'Image') + ':'
    return ""
