# APP/DATABASE/CACHE_DB.PY

# ##PYTHON IMPORTS
import requests

# ##LOCAL IMPORTS
from .. import SESSION
from ..logical.utility import GetCurrentTime, DaysFromNow, GetBufferChecksum
from ..logical.network import GetHTTPFile
from ..logical.file import CreateDirectory, PutGetRaw
from ..cache import ApiData, MediaFile


# ##FUNCTIONS


def GetApiData(data_ids, site_id, type):
    cache_data = []
    for i in range(0, len(data_ids), 100):
        sublist = data_ids[i: i + 100]
        cache_data += _GetApiData(sublist, site_id, type)
    return cache_data


def GetApiArtist(site_artist_id, site_id):
    cache = GetApiData([site_artist_id], site_id, 'artist')
    return cache[0].data if len(cache) else None


def GetApiIllust(site_illust_id, site_id):
    cache = GetApiData([site_illust_id], site_id, 'illust')
    return cache[0].data if len(cache) else None


def SaveApiData(network_data, id_key, site_id, type):
    data_ids = [int(data[id_key]) for data in network_data]
    cache_data = GetApiData(data_ids, site_id, type)
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
            print("SaveApiData - updating cache item:", type, data_id, cache_item.id)
        cache_item.data = data_item
        cache_item.expires = DaysFromNow(1)
    SESSION.commit()


def GetMediaData(image_url, source):
    media = MediaFile.query.filter_by(media_url=image_url).first()
    if media is not None:
        return media
    return _CreateNewMedia(image_url, source)


# #### Private functions


def _GetApiData(data_ids, site_id, type):
    q = ApiData.query
    q = q.filter_by(site_id=site_id, type=type)
    if len(data_ids) == 1:
        q = q.filter_by(data_id=data_ids[0])
    else:
        q = q.filter(ApiData.data_id.in_(data_ids))
    q = q.filter(ApiData.expires > GetCurrentTime())
    return q.all()


def _CreateNewMedia(download_url, source):
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return "Exception processing download: %s" % repr(buffer)
    if isinstance(buffer, requests.Response):
        return "HTTP %d - %s" % (buffer.status_code, buffer.reason)
    md5 = GetBufferChecksum(buffer)
    extension = source.GetMediaExtension(download_url)
    media = MediaFile(md5=md5, file_ext=extension, media_url=download_url, expires=DaysFromNow(1))
    CreateDirectory(media.file_path)
    PutGetRaw(media.file_path, 'wb', buffer)
    SESSION.add(media)
    SESSION.commit()
    return media
