# APP/DATABASE/CACHE_DB.PY

# ##LOCAL IMPORTS
from .. import SESSION
from ..logical.utility import get_current_time, days_from_now, get_buffer_checksum
from ..logical.network import get_http_file
from ..logical.file import create_directory, put_get_raw
from ..models import ApiData, MediaFile


# ##FUNCTIONS


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


def get_media_data(image_url, source):
    media = MediaFile.query.filter_by(media_url=image_url).first()
    if media is not None:
        return media
    return _create_new_media(image_url, source)


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


def _create_new_media(download_url, source):
    buffer = get_http_file(download_url, headers=source.IMAGE_HEADERS)
    if type(buffer) is str:
        return buffer
    md5 = get_buffer_checksum(buffer)
    extension = source.get_media_extension(download_url)
    media = MediaFile(md5=md5, file_ext=extension, media_url=download_url, expires=days_from_now(1))
    create_directory(media.file_path)
    put_get_raw(media.file_path, 'wb', buffer)
    SESSION.add(media)
    SESSION.commit()
    return media
