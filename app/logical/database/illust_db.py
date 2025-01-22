# APP/LOGICAL/DATABASE/ILLUST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.data import swap_key_value

# ## LOCAL IMPORTS
from ...models import Illust, SiteTag, Description
from .illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .tag_db import create_tag_from_parameters, get_tags_by_names
from .base_db import set_column_attributes, set_relationship_collections, set_version_relations,\
    set_timesvalue, add_record, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

SCALAR_RELATIONSHIPS = [('tags', 'name', SiteTag)]
VERSION_RELATIONSHIPS = [('title', 'titles', 'body', Description),
                         ('commentary', 'commentaries', 'body', Description)]

ANY_WRITABLE_COLUMNS = ['site_illust_id', 'site_created', 'pages', 'score', 'active']
NULL_WRITABLE_ATTRIBUTES = ['artist_id', 'site_name', 'title_body', 'commentary_body']


# ## FUNCTIONS

# #### Create

def create_illust_from_parameters(createparams, commit=True):
    createparams.setdefault('active', True)
    swap_key_value(createparams, 'title', 'title_body')
    swap_key_value(createparams, 'commentary', 'commentary_body')
    return set_illust_from_parameters(Illust(), createparams, 'created', commit, True)


def create_illust_from_json(data):
    illust = Illust.loads(data)
    add_record(illust)
    save_record(illust, 'created')
    return illust


# #### Update

def update_illust_from_parameters(illust, updateparams, commit=True, update=True):
    return set_illust_from_parameters(illust, updateparams, 'updated', commit, update)


def update_illust_from_parameters_standard(illust, updateparams):
    """Set parameters that are only removable through direct user interaction before updating."""
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        if 'tags' in updateparams:
            updateparams['tags'] += [name for name in illust.tag_names if name not in updateparams['tags']]
    else:
        # When deactivating automatically, don't allow any other parameters to be set
        updateparams = {'active': False}
    update_illust_from_parameters(illust, updateparams, commit=True, update=False)


def recreate_illust_relations(illust, updateparams):
    if _set_relations(illust, updateparams, False):
        commit_session()


def set_illust_artist(illust, artist):
    illust.artist = artist
    commit_session()


# #### Set

def set_illust_from_parameters(illust, setparams, action, commit, update):
    set_timesvalue(setparams, 'site_created')
    _create_tags(setparams)
    col_result = set_column_attributes(illust, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    rel_result = _set_relations(illust, setparams, update)
    url_result = _set_illust_urls(illust, setparams, update)
    if col_result or rel_result or url_result:
        save_record(illust, action, commit=commit)
    return illust


# #### Query functions

def get_site_illust(site_illust_id, site):
    q = Illust.query
    if isinstance(site, int):
        q = q.filter(Illust.site_id == site)
    elif isinstance(site, str):
        q = q.filter(Illust.site_value == site)
    return q.filter(Illust.site_illust_id == site_illust_id).one_or_none()


def get_site_illusts(site, site_illust_ids, load_urls=False):
    q = Illust.query
    if load_urls:
        q = q.options(selectinload(Illust.urls))
    if isinstance(site, int):
        q = q.filter(Illust.site_id == site)
    elif isinstance(site, str):
        q = q.filter(Illust.site_value == site)
    return q.filter(Illust.site_illust_id.in_(site_illust_ids)).all()


# #### Private functions

def _create_tags(params):
    if 'tags' not in params or len(params['tags']) == 0:
        return
    tags = get_tags_by_names(params['tags'], 'site_tag')
    tags_found = [tag.name for tag in tags]
    for name in params['tags']:
        if name not in tags_found:
            create_tag_from_parameters({'name': name, 'type': 'site_tag'}, commit=False)


def _set_relations(illust, params, update):
    ver_result = set_version_relations(illust, VERSION_RELATIONSHIPS, params, update=update)
    rel_result = set_relationship_collections(illust, SCALAR_RELATIONSHIPS, params, update=update)
    return ver_result or rel_result


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
