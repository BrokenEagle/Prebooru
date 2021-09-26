# APP/DATABASE/CACHE_DB.PY

# ##LOCAL IMPORTS
from .. import SESSION
from ..logical.utility import get_current_time, days_from_now, get_buffer_checksum
from ..logical.network import get_http_file
from ..logical.file import create_directory, put_get_raw
from ..models import ApiData


# ##FUNCTIONS

# ###### CREATE/UPDATE

def save_api_data(network_data, id_key, site_id, type):
    data_ids = [int(data[id_key]) for data in network_data]
    cache_data = get_api_data(data_ids, site_id, type)
    for data_item in network_data:
        data_id = int(data_item[id_key])
        cache_item = next(filter(lambda x: x.data_id == data_id, cache_data), None)
        if not cache_item:
            data = {
                'site_id': site_id,
                'type': type,
                'data_id': data_id,
            }
            cache_item = ApiData(**data)
            SESSION.add(cache_item)
        else:
            print("save_api_data - updating cache item:", type, data_id, cache_item.id)
        cache_item.data = data_item
        cache_item.expires = days_from_now(1)
    SESSION.commit()


# ###### DELETE

def delete_expired_api_data():
    ApiData.query.filter(ApiData.expires < get_current_time()).delete()
    SESSION.commit()


# #### Query functions

def get_api_data(data_ids, site_id, type):
    cache_data = []
    for i in range(0, len(data_ids), 100):
        sublist = data_ids[i: i + 100]
        cache_data += _get_api_data(sublist, site_id, type)
    return cache_data


def get_api_artist(site_artist_id, site_id):
    cache = get_api_data([site_artist_id], site_id, 'artist')
    return cache[0].data if len(cache) else None


def get_api_illust(site_illust_id, site_id):
    cache = get_api_data([site_illust_id], site_id, 'illust')
    return cache[0].data if len(cache) else None


def expired_api_data_count():
    return ApiData.query.filter(ApiData.expires < get_current_time()).get_count()


# #### Private functions


def _get_api_data(data_ids, site_id, type):
    q = ApiData.query
    q = q.filter_by(site_id=site_id, type=type)
    if len(data_ids) == 1:
        q = q.filter_by(data_id=data_ids[0])
    else:
        q = q.filter(ApiData.data_id.in_(data_ids))
    q = q.filter(ApiData.expires > get_current_time())
    return q.all()
