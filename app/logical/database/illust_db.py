# APP/LOGICAL/DATABASE/ILLUST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Illust, IllustUrl, SiteTag, Description
from ..utility import set_error
from .illust_url_db import update_illust_url_from_parameters
from .site_data_db import update_site_data_from_parameters
from .pool_element_db import delete_pool_element
from .base_db import update_column_attributes, update_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'site', 'site_illust_id', 'site_created', 'pages', 'score', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('_tags', 'name', SiteTag)]
APPEND_SCALAR_RELATIONSHIPS = [('_commentaries', 'body', Description)]
ALL_SCALAR_RELATIONSHIPS = UPDATE_SCALAR_RELATIONSHIPS + APPEND_SCALAR_RELATIONSHIPS
ASSOCIATION_ATTRIBUTES = ['tags', 'commentaries']
NORMALIZED_ASSOCIATION_ATTRIBUTES = ['_' + key for key in ASSOCIATION_ATTRIBUTES]

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'site', 'site_illust_id', 'site_created', 'pages', 'score', 'active',
                             '_tags', '_commentaries']
UPDATE_ALLOWED_ATTRIBUTES = ['site', 'site_illust_id', 'site_created', 'pages', 'score', 'active', '_tags',
                             '_commentaries']


# ## FUNCTIONS

# #### Helper functions

# ## MOVE THIS FUNCTION TO PRIVATE SECTION
def set_timesvalues(params):
    set_timesvalue(params, 'site_created')
    set_timesvalue(params, 'site_updated')
    set_timesvalue(params, 'site_uploaded')


# #### Auxiliary functions

# ## MOVE THIS FUNCTION TO PRIVATE SECTION
def update_illust_urls(illust, params):
    update_results = []
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            illust_url = IllustUrl(illust_id=illust.id)
        update_results.append(update_illust_url_from_parameters(illust_url, url_data))
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        SESSION.commit()
        update_results.append(True)
    return any(update_results)


# #### DB functions

# ###### CREATE

def create_illust_from_parameters(createparams):
    current_time = get_current_time()
    set_timesvalues(createparams)
    illust = Illust(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(illust, update_columns, createparams)
    _update_relations(illust, createparams, overwrite=True, create=True)
    print("[%s]: created" % illust.shortlink)
    return illust


def create_illust_from_json(data):
    illust = Illust.loads(data)
    SESSION.add(illust)
    SESSION.commit()
    print("[%s]: created" % illust.shortlink)
    return illust


# ###### UPDATE

def update_illust_from_parameters(illust, updateparams):
    update_results = []
    set_timesvalues(updateparams)
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(illust, update_columns, updateparams))
    update_results.append(_update_relations(illust, updateparams, overwrite=False, create=False))
    if any(update_results):
        print("[%s]: updated" % illust.shortlink)
        illust.updated = get_current_time()
        SESSION.commit()


def recreate_illust_relations(illust, updateparams):
    _update_relations(illust, updateparams, overwrite=True, create=False)


def set_illust_artist(illust, artist):
    illust.artist = artist
    SESSION.commit()


# ###### Delete

def delete_illust(illust):
    for pool_element in illust._pools:
        delete_pool_element(pool_element)
    SESSION.delete(illust)
    SESSION.commit()


# ###### Misc

def illust_delete_commentary(illust, description_id):
    retdata = {'error': False, 'descriptions': [commentary.to_json() for commentary in illust._commentaries]}
    remove_commentary = next((comm for comm in illust._commentaries if comm.id == description_id), None)
    if remove_commentary is None:
        msg = "Commentary with description #%d does not exist on illust #%d." % (description_id, illust.id)
        return set_error(retdata, msg)
    illust._commentaries.remove(remove_commentary)
    SESSION.commit()
    retdata['item'] = illust.to_json()
    return retdata


# #### Query functions

def get_site_illust(site_illust_id, site):
    return Illust.query.filter_by(site=site, site_illust_id=site_illust_id).one_or_none()


def get_site_illusts(site, site_illust_ids, load_urls=False):
    q = Illust.query
    if load_urls:
        q = q.options(selectinload(Illust.urls))
    return q.filter(Illust.site == site, Illust.site_illust_id.in_(site_illust_ids)).all()


# #### Private functions

def _update_relations(illust, updateparams, overwrite=None, create=None):
    update_results = []
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    allowed_attributes = CREATE_ALLOWED_ATTRIBUTES if create else UPDATE_ALLOWED_ATTRIBUTES
    settable_keylist = set(updateparams.keys()).intersection(allowed_attributes)
    relationship_list = ALL_SCALAR_RELATIONSHIPS if overwrite else UPDATE_SCALAR_RELATIONSHIPS
    update_relationships = [rel for rel in relationship_list if rel[0] in settable_keylist]
    update_results.append(update_relationship_collections(illust, update_relationships, updateparams))
    update_results.append(update_site_data_from_parameters(illust, updateparams))
    if not overwrite:
        append_relationships = [rel for rel in APPEND_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
        update_results.append(append_relationship_collections(illust, append_relationships, updateparams))
    if 'illust_urls' in updateparams:
        update_results.append(update_illust_urls(illust, updateparams['illust_urls']))
    return any(update_results)
