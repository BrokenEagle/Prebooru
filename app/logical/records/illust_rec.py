# APP/LOGICAL/RECORDS/ILLUST_REC.PY

# ## PACKAGE IMPORTS
from utility.data import merge_dicts

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..database.artist_db import get_site_artist
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters, delete_illust,\
    get_site_illust, create_illust_from_raw_parameters
from ..database.illust_url_db import get_illust_url_by_url
from ..database.post_db import post_append_illust_url, get_post_by_md5
from ..database.notation_db import create_notation_from_raw_parameters
from ..database.archive_data_db import get_archive_data, create_archive_data, update_archive_data
from .artist_rec import create_artist_from_source


# ## FUNCTIONS

def create_illust_from_source(site_illust_id, source):
    createparams = source.get_illust_data(site_illust_id)
    if not createparams['active']:
        return
    artist = get_site_artist(createparams['site_artist_id'], source.SITE_ID)
    if artist is None:
        artist = create_artist_from_source(createparams['site_artist_id'], source)
        if artist is None:
            return
    createparams['artist_id'] = artist.id
    return create_illust_from_parameters(createparams)


def update_illust_from_source(illust, source):
    updateparams = source.get_illust_data(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag for tag in illust.tags if tag not in updateparams['tags']]
    update_illust_from_parameters(illust, updateparams)


def archive_illust_for_deletion(illust):
    retdata = {'error': False}
    retdata = _archive_illust_data(illust, retdata)
    if retdata['error']:
        return retdata
    return _delete_illust_data(illust, retdata)


def recreate_archived_illust(data):
    retdata = {'error': False}
    illust_data = data['body']
    illust = get_site_illust(illust_data['site_illust_id'], illust_data['site_id'])
    if illust is not None:
        return set_error(retdata, "Illust already exists: illust #%d" % illust.id)
    artist = get_site_artist(data['links']['artist']['site_artist_id'], data['links']['artist']['site_id'])
    if artist is None:
        return set_error(retdata, "Artist for illust does not exist.")
    illust_data['artist_id'] = artist.id
    merge_dicts(illust_data, data['relations']['site_data'])
    if len(data['scalars']['tags']):
        illust_data['tags'] = data['scalars']['tags']
    if len(data['scalars']['commentaries']):
        illust_data['commentaries'] = data['scalars']['commentaries']
    if len(data['relations']['illust_urls']):
        illust_data['illust_urls'] = data['relations']['illust_urls']
    try:
        illust = create_illust_from_raw_parameters(data['body'])
    except Exception as e:
        return set_error(retdata, "Error creating illust: %s" % str(e))
    retdata['item'] = illust.to_json()
    relink_archived_illust(data, illust)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_raw_parameters(notation_data)
        illust.notations.append(notation)
        SESSION.commit()
    return retdata


def relink_archived_illust(data, illust=None):
    if illust is None:
        illust = get_site_illust(data['body']['site_illust_id'], data['body']['site_id'])
        if illust is None:
            return "No illust found with site ID %d" % data['body']['site_illust_id']
    for link_data in data['links']['posts']:
        illust_url = get_illust_url_by_url(site_id=link_data['site_id'], partial_url=link_data['url'])
        if illust_url is None:
            return
        post = get_post_by_md5(link_data['md5'])
        if post is not None:
            post_append_illust_url(post, illust_url)


# #### Private functions

def _archive_illust_data(illust, retdata):
    data = {
        'body': illust.archive_dict(),
        'scalars': {
            'commentaries': list(illust.commentaries),
            'tags': list(illust.tags),
        },
        'relations': {
            'illust_urls': [illust_url.archive_dict() for illust_url in illust.urls],
            'site_data': illust.site_data.archive_dict(),
            'notations': [notation.archive_dict() for notation in illust.notations],
        },
        'links': {
            'artist': {
                'site_id': illust.artist.site_id,
                'site_artist_id': illust.artist.site_artist_id,
            },
            'posts': [{'md5': illust_url.post.md5, 'url': illust_url.url, 'site_id': illust_url.site_id}
                      for illust_url in illust.urls if illust_url.post is not None],
        },
    }
    data_key = '%d-%d' % (illust.site_id, illust.site_illust_id)
    archive_data = get_archive_data('illust', data_key)
    try:
        if archive_data is None:
            create_archive_data('illust', data_key, data, 30)
        else:
            update_archive_data(archive_data, data, 30)
    except Exception as e:
        return set_error(retdata, "Error archiving data: %s" % str(e))
    return retdata


def _delete_illust_data(illust, retdata):
    try:
        delete_illust(illust)
    except Exception as e:
        SESSION.rollback()
        return set_error(retdata, "Error deleting illust: %s" % str(e))
    return retdata
