# APP/LOGICAL/DATABASE/ILLUST_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.data import swap_key_value
from utility.uprint import buffered_print

# ## LOCAL IMPORTS
from ...models import Illust
from .illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .base_db import set_column_attributes, set_relationship_collections, set_version_relations,\
    set_timesvalue, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

SCALAR_RELATIONSHIPS = ['tag_names']
VERSION_RELATIONSHIPS = [('title_body', 'title_bodies'), ('commentary_body', 'commentary_bodies')]

ANY_WRITABLE_ATTRIBUTES = ['site_illust_id', 'site_url', 'site_created', 'pages', 'score', 'active']
NULL_WRITABLE_ATTRIBUTES = ['artist_id', 'site_name', 'created', 'updated']
CREATE_ONLY_ATTRIBUTES = ['title_body', 'commentary_body']


# ## FUNCTIONS

# #### Create

def create_illust_from_parameters(createparams, commit=True):
    createparams.setdefault('active', True)
    set_timesvalue(createparams, 'created')
    set_timesvalue(createparams, 'updated')
    return set_illust_from_parameters(Illust(), createparams, 'created', commit, True)


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


def set_illust_artist(illust, artist):
    print("[%s]: Changing to %s" % (illust.shortlink, artist.shortlink))
    illust.artist = artist
    commit_session()


# #### Set

def set_illust_from_parameters(illust, setparams, action, commit, update):
    swap_key_value(setparams, 'tags', 'tag_names')
    swap_key_value(setparams, 'title', 'title_body')
    swap_key_value(setparams, 'commentary', 'commentary_body')
    set_timesvalue(setparams, 'site_created')
    col_result = set_column_attributes(illust, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams,
                                       create_attributes=CREATE_ONLY_ATTRIBUTES, update=update, safe=True)
    ver_result = set_version_relations(illust, VERSION_RELATIONSHIPS, setparams, update=update)\
        if action == 'updated' else False
    rel_result = set_relationship_collections(illust, SCALAR_RELATIONSHIPS, setparams, update=update)
    url_result = _set_illust_urls(illust, setparams, update)
    if col_result or ver_result or rel_result or url_result:
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


# #### Private functions

def _set_illust_urls(illust, params, update):
    if 'illust_urls' not in params:
        return False
    printer = buffered_print('set_column_attributes', safe=True, header=False)
    update_results = False
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params['illust_urls']:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            url_data['illust_id'] = illust.id
            illust_url = create_illust_url_from_parameters(url_data)
            printer(f"set_illust_urls: {illust_url.shortlink} created")
            update_results = True
        else:
            temp_illust_url = illust_url.copy()
            update_illust_url_from_parameters(illust_url, url_data)
            if illust_url != temp_illust_url:
                printer(f"set_illust_urls: {illust_url.shortlink} updated")
                update_results = True
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        # These will only be removable via the illust urls controller
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        printer(f"set_illust_urls: {illust_url.shortlink} inactivated")
        update_results = True
    if update_results:
        if update:
            illust.updated = get_current_time()
        flush_session()
        printer.print()
    return update_results
