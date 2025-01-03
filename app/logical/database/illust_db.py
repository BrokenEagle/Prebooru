# APP/LOGICAL/DATABASE/ILLUST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Illust, SiteTag, Description
from ..utility import set_error
from .illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .site_data_db import create_site_data_from_parameters, update_site_data_from_parameters
from .tag_db import create_tag_from_parameters, get_tags_by_names
from .base_db import set_column_attributes, set_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes, add_record, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

UPDATE_SCALAR_RELATIONSHIPS = [('_tags', 'name', SiteTag)]
APPEND_SCALAR_RELATIONSHIPS = [('_commentaries', 'body', Description)]
ASSOCIATION_ATTRIBUTES = ['tags', 'commentaries']

ANY_WRITABLE_COLUMNS = ['site_illust_id', 'site_created', 'pages', 'score', 'active']
NULL_WRITABLE_ATTRIBUTES = ['artist_id', 'site_id']


# ## FUNCTIONS

# #### Create

def create_illust_from_parameters(createparams, commit=True):
    illust = Illust()
    return set_illust_from_parameters(illust, createparams, 'created', commit, True)


def create_illust_from_json(data):
    illust = Illust.loads(data)
    add_record(illust)
    save_record(illust, 'created')
    return illust


# #### Update

def update_illust_from_parameters(illust, updateparams, commit=True, update=True):
    return set_illust_from_parameters(illust, updateparams, 'updated', commit, update)


def recreate_illust_relations(illust, updateparams):
    if _set_relations(illust, updateparams):
        commit_session()


def set_illust_artist(illust, artist):
    illust.artist = artist
    commit_session()


# #### Set

def set_illust_from_parameters(illust, setparams, action, commit, update):
    if 'site' in setparams:
        setparams['site_id'] = Illust.site_enum.by_name(setparams['site']).id
    set_timesvalue(setparams, 'site_created')
    set_timesvalue(setparams, 'site_updated')
    set_timesvalue(setparams, 'site_uploaded')
    _create_tags(setparams)
    col_result = set_column_attributes(illust, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    rel_result = _set_relations(illust, setparams, update)
    url_result = _set_illust_urls(illust, setparams, update)
    if col_result or rel_result or url_result:
        save_record(illust, action, commit=commit)
    return illust


# #### Misc

def illust_delete_commentary(illust, description_id):
    retdata = {'error': False, 'descriptions': [commentary.to_json() for commentary in illust._commentaries]}
    remove_commentary = next((comm for comm in illust._commentaries if comm.id == description_id), None)
    if remove_commentary is None:
        msg = "Commentary with description #%d does not exist on illust #%d." % (description_id, illust.id)
        return set_error(retdata, msg)
    illust._commentaries.remove(remove_commentary)
    commit_session()
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

def _create_tags(params):
    if 'tags' not in params:
        return
    tags = get_tags_by_names(params['tags'], 'site_tag')
    tags_found = [tag.name for tag in tags]
    dirty = False
    for name in params['tags']:
        if name not in tags_found:
            create_tag_from_parameters({'name': name, 'type': 'site_tag'}, commit=False)
            dirty = True
    if dirty:
        commit_session()


def _set_relations(illust, setparams, update):
    if isinstance(setparams.get('commentaries'), str):
        setparams['_commentaries_append'] = setparams['commentaries']
        setparams['commentaries'] = None
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    set_rel_result = set_relationship_collections(illust, UPDATE_SCALAR_RELATIONSHIPS, setparams, update=update)
    append_rel_result = append_relationship_collections(illust, APPEND_SCALAR_RELATIONSHIPS, setparams, update=update)
    setparams['illust_id'] = illust.id
    setparams['site'] = illust.site.name
    if illust.site_data is None:
        site_data_result = create_site_data_from_parameters(setparams)
    else:
        site_data_result = update_site_data_from_parameters(illust.site_data, setparams)
    return any([set_rel_result, append_rel_result, site_data_result])


def _set_illust_urls(illust, params, update):
    if 'illust_urls' not in params:
        return False
    update_results = False
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params['illust_urls']:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            url_data['illust_id'] = illust.id
            illust_url = create_illust_url_from_parameters(url_data)
            update_results = True
        else:
            temp_illust_url = illust_url.copy()
            update_illust_url_from_parameters(illust_url, url_data)
            update_results = update_results or illust_url.compare(temp_illust_url)
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        # These will only be removable via the illust urls controller
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        update_results = True
    if update_results:
        if update:
            illust.updated = get_current_time()
        flush_session()
    return update_results


def _enum_filter(site):
    if isinstance(site, int):
        return Illust.site_filter('id', '__eq__', site)
    elif isinstance(site, str):
        return Illust.site_filter('name', '__eq__', site)
