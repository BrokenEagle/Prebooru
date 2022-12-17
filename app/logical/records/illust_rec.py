# APP/LOGICAL/RECORDS/ILLUST_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..sources.base import get_media_source
from ..database.artist_db import get_site_artist, get_blank_artist
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters, delete_illust,\
    get_site_illust, create_illust_from_json, recreate_illust_relations
from ..database.illust_url_db import get_illust_url_by_url, set_url_site
from ..database.post_db import post_append_illust_url, get_post_by_md5
from ..database.notation_db import create_notation_from_json
from ..database.archive_db import get_archive, create_archive, update_archive
from .artist_rec import get_or_create_artist_from_source


# ## FUNCTIONS

def create_illust_from_source(site_illust_id, source):
    createparams = source.get_illust_data(site_illust_id)
    if not createparams['active']:
        return
    artist = get_or_create_artist_from_source(createparams['site_artist_id'], source)
    if artist is None:
        return
    createparams['artist_id'] = artist.id
    return create_illust_from_parameters(createparams)


def update_illust_from_source(illust):
    source = illust.site.source
    updateparams = source.get_illust_data(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag for tag in illust.tags if tag not in updateparams['tags']]
    update_illust_from_parameters(illust, updateparams)
    if 'site_artist_id' in updateparams and illust.artist.site_artist_id != updateparams['site_artist_id']:
        artist = get_or_create_artist_from_source(updateparams['site_artist_id'], source)
        if artist is None:
            artist = get_blank_artist()
        print_warning(f"[{illust.shortlink}] Switching artist from {illust.artist.shortlink} to {artist.shortlink}")
        illust.artist = artist
        SESSION.commit()


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
    artist_data = data['links']['artist']
    artist = get_site_artist(artist_data['site_artist_id'], artist_data['site_id'])
    if artist is None:
        return set_error(retdata, "Artist for illust does not exist.")
    illust_data['artist_id'] = artist.id
    illust = create_illust_from_json(illust_data)
    updateparams = (data['relations'].get('site_data') or {}).copy()
    if len(data['scalars']['tags']):
        updateparams['tags'] = data['scalars']['tags']
    if len(data['scalars']['commentaries']):
        updateparams['commentaries'] = data['scalars']['commentaries']
    if len(data['relations']['illust_urls']):
        updateparams['illust_urls'] = data['relations']['illust_urls']
        for illust_url_data in updateparams['illust_urls']:
            source = get_media_source(illust_url_data['url'])
            set_url_site(illust_url_data, source)
    recreate_illust_relations(illust, updateparams)
    retdata['item'] = illust.to_json()
    relink_archived_illust(data, illust)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_json(notation_data)
        illust.notations.append(notation)
        SESSION.commit()
    return retdata


def relink_archived_illust(data, illust=None):
    if illust is None:
        illust = get_site_illust(data['body']['site_illust_id'], data['body']['site_id'])
        if illust is None:
            return "No illust found with site ID %d" % data['body']['site_illust_id']
    for link_data in data['links']['posts']:
        illust_url = get_illust_url_by_url(site=link_data['site'], partial_url=link_data['url'])
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
            'site_data': illust.site_data.archive_dict() if illust.site_data is not None else None,
            'notations': [notation.archive_dict() for notation in illust.notations],
        },
        'links': {
            'artist': {
                'site': illust.artist.site,
                'site_artist_id': illust.artist.site_artist_id,
            },
            'posts': [{'md5': illust_url.post.md5, 'url': illust_url.url, 'site': illust_url.site}
                      for illust_url in illust.urls if illust_url.post is not None],
        },
    }
    data_key = '%d-%d' % (illust.site, illust.site_illust_id)
    archive = get_archive('illust', data_key)
    try:
        if archive is None:
            create_archive('illust', data_key, data, 30)
        else:
            update_archive(archive, data, 30)
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
