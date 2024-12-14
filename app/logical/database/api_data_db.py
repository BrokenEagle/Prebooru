# APP/LOGICAL/DATABASE/API_DATA_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ...models import ApiData
from .base_db import add_record, delete_record, commit_session


# ## FUNCTIONS

# ###### CREATE/UPDATE

def save_api_data(network_data, id_key, site_id, type_id):
    data_ids = [int(data[id_key]) for data in network_data]
    cache_data = get_api_data(data_ids, site_id, type_id)
    for data_item in network_data:
        data_id = int(data_item[id_key])
        cache_item = next(filter(lambda x: x.data_id == data_id, cache_data), None)
        if not cache_item:
            print("save_api_data - creating cache item:", type_id, data_id)
            data = {
                'site_id': site_id,
                'type_id': type_id,
                'data_id': data_id,
            }
            cache_item = ApiData(**data)
            add_record(cache_item)
        else:
            print("save_api_data - updating cache item:", type_id, data_id, cache_item.id)
        cache_item.data = data_item
        cache_item.expires = days_from_now(1)
    commit_session()


# ###### DELETE

def delete_expired_api_data():
    ApiData.query.filter(ApiData.expires < get_current_time()).delete()
    commit_session()


# #### Query functions

def get_api_data(data_ids, site, type):
    current_time = get_current_time()
    has_deleted = False
    cache_data = []
    for i in range(0, len(data_ids), 100):
        sublist = data_ids[i: i + 100]
        cache_data += _get_api_data(sublist, site, type)
    ret_data = []
    for cache in cache_data:
        if cache.expires < current_time:
            delete_record(cache)
            has_deleted = True
        else:
            ret_data.append(cache)
    if has_deleted:
        commit_session()
    return ret_data


def get_api_artist(site_artist_id, site):
    cache = get_api_data([site_artist_id], site, 'artist')
    return cache[0].data if len(cache) else None


def get_api_illust(site_illust_id, site):
    cache = get_api_data([site_illust_id], site, 'illust')
    return cache[0].data if len(cache) else None


def expired_api_data_count():
    return ApiData.query.filter(ApiData.expires < get_current_time()).get_count()


# #### Private functions

def _get_api_data(data_ids, site, type):
    if isinstance(site, int):
        site_enum_filter = ApiData.site_filter('id', '__eq__', site)
    elif isinstance(site, str):
        site_enum_filter = ApiData.site_filter('name', '__eq__', site)
    if isinstance(type, int):
        type_enum_filter = ApiData.type_filter('id', '__eq__', type)
    elif isinstance(type, str):
        type_enum_filter = ApiData.type_filter('name', '__eq__', type)
    q = ApiData.query.enum_join(ApiData.site_enum).enum_join(ApiData.type_enum)\
                     .filter(site_enum_filter, type_enum_filter)
    if len(data_ids) == 1:
        q = q.filter(ApiData.data_id == data_ids[0])
    else:
        q = q.filter(ApiData.data_id.in_(data_ids))
    return q.all()
