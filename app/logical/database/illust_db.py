# APP/LOGICAL/DATABASE/ILLUST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Illust, SiteTag, Description
from ..utility import set_error
from .illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .site_data_db import update_site_data_from_parameters
from .pool_element_db import delete_pool_element
from .base_db import set_column_attributes, set_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes, commit_or_flush, save_record, add_record, delete_record


# ## GLOBAL VARIABLES

UPDATE_SCALAR_RELATIONSHIPS = [('_tags', 'name', SiteTag)]
APPEND_SCALAR_RELATIONSHIPS = [('_commentaries', 'body', Description)]
ALL_SCALAR_RELATIONSHIPS = UPDATE_SCALAR_RELATIONSHIPS + APPEND_SCALAR_RELATIONSHIPS
ASSOCIATION_ATTRIBUTES = ['tags', 'commentaries']
NORMALIZED_ASSOCIATION_ATTRIBUTES = ['_' + key for key in ASSOCIATION_ATTRIBUTES]

ANY_WRITABLE_COLUMNS = ['site_illust_id', 'site_created', 'pages', 'score', 'active']
NULL_WRITABLE_ATTRIBUTES = ['artist_id', 'site_id']


# ## FUNCTIONS

# #### CREATE

def create_illust_from_parameters(createparams, commit=True):
    return set_illust_from_parameters(Illust(), createparams, commit, 'created', False)


def create_illust_from_json(data):
    illust = Illust.loads(data)
    add_record(illust)
    commit_or_flush(True)
    print("[%s]: created" % illust.shortlink)
    return illust


# #### UPDATE

def update_illust_from_parameters(illust, updateparams, commit=True, update=False):
    return set_illust_from_parameters(illust, updateparams, commit, 'updated', update)


def recreate_illust_relations(illust, updateparams):
    _set_relations(illust, updateparams)
    commit_or_flush(True)


def set_illust_artist(illust, artist):
    illust.artist = artist
    commit_or_flush(True)


# #### Set

def set_illust_from_parameters(illust, setparams, commit, action, update):
    if 'site' in setparams:
        setparams['site_id'] = Illust.site_enum.by_name(setparams['site']).id
    set_timesvalue(setparams, 'site_created')
    set_timesvalue(setparams, 'site_updated')
    set_timesvalue(setparams, 'site_uploaded')
    col_result = set_column_attributes(illust, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update)
    if col_result:
        commit_or_flush(False, safe=True)
    rel_result = _set_relations(illust, setparams)
    url_result = _set_illust_urls(illust, setparams)
    if update and (rel_result or url_result):
        illust.updated = get_current_time()
    if col_result or rel_result or url_result:
        save_record(illust, commit, action)
    return illust


# ###### Delete

def delete_illust(illust):
    for pool_element in illust._pools:
        delete_pool_element(pool_element)
    delete_record(illust)
    commit_or_flush(True)


def illust_delete_commentary(illust, description_id):
    retdata = {'error': False, 'descriptions': [commentary.to_json() for commentary in illust._commentaries]}
    remove_commentary = next((comm for comm in illust._commentaries if comm.id == description_id), None)
    if remove_commentary is None:
        msg = "Commentary with description #%d does not exist on illust #%d." % (description_id, illust.id)
        return set_error(retdata, msg)
    illust._commentaries.remove(remove_commentary)
    commit_or_flush(True)
    retdata['item'] = illust.to_json()
    return retdata


# #### Query functions

def get_site_illust(site_illust_id, site):
    return Illust.query.enum_join(Illust.site_enum)\
                       .filter(_enum_filter(site), Illust.site_illust_id == site_illust_id)\
                       .one_or_none()


def get_site_illusts(site, site_illust_ids, load_urls=False):
    q = Illust.query
    if load_urls:
        q = q.options(selectinload(Illust.urls))
    return q.enum_join(Illust.site_enum)\
            .filter(_enum_filter(site), Illust.site_illust_id.in_(site_illust_ids))\
            .all()


# #### Private functions

def _set_relations(illust, setparams):
    if isinstance(setparams.get('commentaries'), str):
        setparams['_commentaries_append'] = setparams['commentaries']
        setparams['commentaries'] = None
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    set_rel_result = set_relationship_collections(illust, ALL_SCALAR_RELATIONSHIPS, setparams)
    append_rel_result = append_relationship_collections(illust, APPEND_SCALAR_RELATIONSHIPS, setparams)
    site_data_result = update_site_data_from_parameters(illust, setparams, commit=False)
    return any([set_rel_result, append_rel_result, site_data_result])


def _set_illust_urls(illust, params):
    if 'illust_urls' not in params:
        return False
    update_results = False
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params['illust_urls']:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            url_data['illust_id'] = illust.id
            illust_url = create_illust_url_from_parameters(url_data, commit=False)
            update_results = True
        else:
            temp_illust_url = illust_url.copy()
            update_illust_url_from_parameters(illust_url, url_data, commit=False)
            update_results = update_results or illust_url.compare(temp_illust_url)
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        # These will only be removable via the illust urls controller
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        commit_or_flush(False)
        update_results = True
    return update_results


def _enum_filter(site):
    if isinstance(site, int):
        return Illust.site_filter('id', '__eq__', site)
    elif isinstance(site, str):
        return Illust.site_filter('name', '__eq__', site)
