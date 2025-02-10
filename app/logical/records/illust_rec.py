# APP/LOGICAL/RECORDS/ILLUST_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_warning
from utility.data import merge_dicts

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import IllustTitles, IllustCommentaries, AdditionalCommentaries, Description, ArchiveIllust
from ..logger import handle_error_message
from ..network import get_http_data
from ..utility import set_error
from ..sites import site_name_by_url
from ..database.base_db import delete_record, commit_session, get_or_create
from ..database.artist_db import get_blank_artist, get_site_artist
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters_standard,\
    get_site_illust
from ..database.illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from ..database.post_db import get_posts_by_md5s
from ..database.notation_db import create_notation_from_parameters
from ..database.archive_db import create_archive_from_parameters, update_archive_from_parameters,\
    get_archive_by_illust_site
from ..database.archive_illust_db import create_archive_illust_from_parameters, update_archive_illust_from_parameters
from ..database.download_db import create_download_from_parameters, update_download_from_parameters,\
    get_download_by_request_url
from ..database.download_element_db import create_download_element_from_parameters,\
    update_download_element_from_parameters, get_download_element
from .base_rec import delete_data
from .artist_rec import get_or_create_artist_from_source
from .pool_rec import delete_pool_element


# ## GLOBAL VARIABLES

COMMENTARY_MODELS = {
    'old': IllustCommentaries,
    'additional': AdditionalCommentaries,
}


# ## FUNCTIONS

# #### Illusts

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
    source = illust.source
    updateparams = source.get_illust_data(illust.site_illust_id)
    update_illust_from_parameters_standard(illust, updateparams)
    if 'site_artist_id' in updateparams and illust.artist.site_artist_id != updateparams['site_artist_id']:
        artist = get_or_create_artist_from_source(updateparams['site_artist_id'], source)
        if artist is None:
            artist = get_blank_artist()
        print_warning(f"[{illust.shortlink}] Switching artist from {illust.artist.shortlink} to {artist.shortlink}")
        illust.artist = artist
        SESSION.commit()


def delete_illust(illust, retdata=None):
    """Hard delete. Continue as long as illust record gets deleted."""

    def _delete(illust):
        msg = "[%s]: deleted\n" % illust.shortlink
        for pool_element in illust._pools:
            delete_pool_element(pool_element)
        delete_record(illust)
        commit_session()
        print(msg)

    retdata = retdata or {'error': False, 'is_deleted': False}
    retdata.update(delete_data(illust, _delete))
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    return retdata


def archive_illust_for_deletion(illust, days_to_expire):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    retdata.update(save_illust_to_archive(illust, days_to_expire))
    if retdata['error']:
        return retdata
    return delete_illust(illust, retdata)


def save_illust_to_archive(illust, days_to_expire):
    retdata = {'error': False}
    archive = get_archive_by_illust_site(illust.site_id, illust.site_illust_id)
    if archive is None:
        archive = create_archive_from_parameters({'days': days_to_expire, 'type_name': 'illust'}, commit=False)
    else:
        update_archive_from_parameters(archive, {'days': days_to_expire}, commit=False)
    retdata['item'] = archive.basic_json()
    archive_params = {k: v for (k, v) in illust.basic_json().items() if k in ArchiveIllust.basic_attributes}
    archive_params['site_artist_id'] = illust.artist.site_artist_id
    archive_params['title'] = illust.title_body
    archive_params['commentary'] = illust.commentary_body
    archive_params['urls_json'] = [{'order': illust_url.order,
                                    'url': illust_url.full_url,
                                    'sample': illust_url.full_sample_url,
                                    'height': illust_url.height,
                                    'width': illust_url.width,
                                    'active': illust_url.active,
                                    'md5': illust_url.md5}
                                   for illust_url in illust.urls]
    archive_params['titles_json'] = list(illust.title_bodies)
    archive_params['commentaries_json'] = list(illust.commentary_bodies)
    archive_params['additional_commentaries_json'] = list(illust.additional_commentary_bodies)
    archive_params['tags_json'] = list(illust.tag_names)
    archive_params['notations_json'] = [{'body': notation.body,
                                         'created': notation.created.isoformat(),
                                         'updated': notation.updated.isoformat()}
                                        for notation in illust.notations]
    if archive.illust_data is None:
        archive_params['archive_id'] = archive.id
        create_archive_illust_from_parameters(archive_params)
    else:
        update_archive_illust_from_parameters(archive.illust_data, archive_params)
    return retdata


def recreate_archived_illust(archive):
    illust_data = archive.illust_data
    illust = get_site_illust(illust_data.site_illust_id, illust_data.site_id)
    if illust is not None:
        return handle_error_message(f"Illust already exists: {illust.shortlink}")
    artist = get_site_artist(illust_data.site_artist_id, illust_data.site_id)
    if artist is None:
        msg = f"Artist for illust does not exist: {illust_data.site_name} #{illust_data.site_artist_id}"
        return handle_error_message(msg)
    createparams = merge_dicts(illust_data.recreate_json(), {'artist_id': artist.id})
    illust = create_illust_from_parameters(createparams, commit=False)
    source = illust.source
    illust_urls = []
    for url_data in illust_data.urls_json:
        url_data['illust_id'] = illust.id
        if 'url' in url_data and url_data['url'].startswith('http'):
            url_data['site_name'] = site_name_by_url(url_data['url'])
            url_data['url'] = source.partial_media_url(url_data['url'])
        if 'sample' in url_data and url_data['sample'] is not None and url_data['sample'].startswith('http'):
            url_data['sample_site_name'] = site_name_by_url(url_data['sample'])
            url_data['sample_url'] = source.partial_media_url(url_data['sample'])
        illust_url = create_illust_url_from_parameters(url_data, commit=False)
        illust_urls.append(illust_url)
    illust.tag_names.extend(illust_data.tags_json)
    illust.title_bodies.extend(illust_data.titles_json)
    illust.commentary_bodies.extend(illust_data.commentaries_json)
    illust.additional_commentary_bodies.extend(illust_data.additional_commentaries_json)
    _link_illust_urls(illust_urls, illust_data)
    for notation in illust_data.notations_json:
        createparams = merge_dicts(notation, {'illust_id': illust.id})
        create_notation_from_parameters(createparams, commit=False)
    retdata = {'error': False, 'item': illust.basic_json()}
    commit_session()
    update_archive_from_parameters(archive, {'days': 7})
    return retdata


def relink_archived_illust(archive):
    illust_data = archive.illust_data
    if illust_data.urls is None:
        return handle_error_message("No urls data on archive record.")
    illust = get_site_illust(illust_data.site_illust_id, illust_data.site_id)
    if illust is None:
        msg = f"{illust_data.site_name} #{illust_data.site_artist_id} not found in illusts."
        return handle_error_message(msg)
    retdata = {'error': False, 'item': illust.basic_json()}
    _link_illust_urls(illust.urls, illust_data)
    commit_session()
    return retdata


def illust_delete_title(illust, description_id):
    retdata = _relation_params_check(illust, Description, IllustTitles, description_id, 'description_id', 'Title')
    if retdata['error']:
        return retdata
    IllustTitles.query.filter_by(illust_id=illust.id, description_id=description_id).delete()
    commit_session()
    return retdata


def illust_swap_title(illust, description_id):
    retdata = _relation_params_check(illust, Description, IllustTitles, description_id, 'description_id', 'Title')
    if retdata['error']:
        return retdata
    IllustTitles.query.filter_by(illust_id=illust.id, description_id=description_id).delete()
    swap = illust.title
    illust.title = retdata['attach']
    if swap is not None:
        illust.titles.append(swap)
    commit_session()
    return retdata


def illust_delete_commentary(rel_type, illust, description_id):
    secondary_table = COMMENTARY_MODELS[rel_type]
    retdata = _relation_params_check(illust, Description, secondary_table, description_id, 'description_id', 'Title')
    if retdata['error']:
        return retdata
    secondary_table.query.filter_by(illust_id=illust.id, description_id=description_id).delete()
    commit_session()
    return retdata


def illust_swap_commentary(illust, description_id):
    retdata = _relation_params_check(illust, Description, IllustCommentaries, description_id, 'description_id', 'Title')
    if retdata['error']:
        return retdata
    IllustCommentaries.query.filter_by(illust_id=illust.id, description_id=description_id).delete()
    swap = illust.commentary
    illust.commentary = retdata['attach']
    if swap is not None:
        illust.commentaries.append(swap)
    commit_session()
    return retdata


def illust_add_additional_commentary(illust, commentary):
    retdata = {'error': False}
    descr = get_or_create(Description, 'body', commentary)
    m2m_row = AdditionalCommentaries.query.filter_by(illust_id=illust.id, description_id=descr.id).one_or_none()
    if m2m_row is not None:
        return set_error(retdata, "Commentary already included on %s." % illust.shortlink)
    illust.additional_commentaries.append(descr)
    commit_session()
    return retdata


# #### Illust URLs

def download_illust_url(illust_url):
    retdata = {'errors': [], 'buffer': None}
    buffer = _download_media(illust_url.original_url, illust_url.source.IMAGE_HEADERS)
    if isinstance(buffer, tuple):
        retdata['errors'].append(buffer)
        if illust_url.alternate_url:
            buffer = _download_media(illust_url.alternate_url, illust_url.source.IMAGE_HEADERS)
            if isinstance(buffer, tuple):
                retdata['errors'].append(buffer)
            else:
                retdata['buffer'] = buffer
    else:
        retdata['buffer'] = buffer
    return retdata


def download_illust_sample(illust_url):
    retdata = {'errors': [], 'buffer': None}
    buffer = _download_media(illust_url.original_sample_url, illust_url.source.IMAGE_HEADERS)
    if isinstance(buffer, tuple):
        retdata['errors'].append(buffer)
        if illust_url.alternate_url:
            buffer = _download_media(illust_url.alternate_sample_url, illust_url.source.IMAGE_HEADERS)
            if isinstance(buffer, tuple):
                retdata['errors'].append(buffer)
            else:
                retdata['buffer'] = buffer
    else:
        retdata['buffer'] = buffer
    return retdata


def create_download_from_illust_url(illust_url):
    from .download_rec import create_post_from_download_element
    illust = illust_url.illust
    illust_download = get_download_by_request_url(illust.key)
    if illust_download is None:
        illust_download = create_download_from_parameters({'request_url': illust.key, 'status_name': 'processing'})
    else:
        update_download_from_parameters(illust_download, {'status_name': 'processing'})
    illust_url_element = get_download_element(illust_download.id, illust_url.id)
    if illust_url_element is None:
        params = {
            'download_id': illust_download.id,
            'illust_url_id': illust_url.id,
        }
        illust_url_element = create_download_element_from_parameters(params)
    else:
        update_download_element_from_parameters(illust_url_element, {'status_name': 'pending'})
    create_post_from_download_element(illust_url_element)
    retdata = {'error': False}
    if illust_url_element.status_name == 'complete':
        update_download_from_parameters(illust_download, {'status_name': 'complete'})
    else:
        # Setting the unknown status so that it can't be restarted from the download UI
        update_download_from_parameters(illust_download, {'status_name': 'unknown'})
        retdata = set_error(retdata, "Error downloading post on %s." % illust_url_element.shortlink)
    return retdata


# #### Private functions

def _download_media(download_url, headers):
    print("Downloading", download_url)
    buffer = get_http_data(download_url, headers=headers)
    if isinstance(buffer, str):
        return _module_error('download_media', "Download URL: %s => %s" % (download_url, buffer))
    return buffer


def _module_error(function, message):
    return (f'illust_rec.{function}', message)


# ## Private functions

def _relation_params_check(illust, model, m2m_model, model_id, model_field, name):
    retdata = {'error': False}
    attach = model.find(model_id)
    if attach is None:
        return set_error(retdata, "%s #%d does not exist." % (model.model_name, model_id))
    retdata['attach'] = attach
    m2m_row = m2m_model.query.filter_by(**{'illust_id': illust.id, model_field: model_id}).one_or_none()
    if m2m_row is None:
        msg = "%s with %s does not exist on %s." % (name, attach.shortlink, illust.shortlink)
        return set_error(retdata, msg)
    return retdata


def _link_illust_urls(illust_urls, illust_data):
    md5s = [data['md5'] for data in illust_data.urls_json if data['md5'] is not None]
    if len(md5s) == 0:
        return
    posts = get_posts_by_md5s(md5s)
    for post in posts:
        url_data = next(data for data in illust_data.urls_json if data['md5'] == post.md5)
        illust_url = next(iu for iu in illust_urls if iu.full_url == url_data['url'])
        update_illust_url_from_parameters(illust_url, {'post_id': post.id}, commit=False)
