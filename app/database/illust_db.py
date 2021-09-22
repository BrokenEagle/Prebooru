# APP/DATABASE/ARTIST_DB.PY

# ##PYTHON IMPORTS
import datetime

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import get_current_time, set_error
from .base_db import update_column_attributes, update_relationship_collections, append_relationship_collections, set_timesvalue
from .artist_db import create_artist_from_source, get_site_artist
from .illust_url_db import update_illust_url_from_parameters
from .site_data_db import update_site_data_from_parameters


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('tags', 'name', models.Tag)]
APPEND_SCALAR_RELATIONSHIPS = [('commentaries', 'body', models.Description)]

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active', 'tags', 'commentaries']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active', 'tags', 'commentaries']


# ## FUNCTIONS

# #### Helper functions

def set_timesvalues(params):
    set_timesvalue(params, 'site_created')
    set_timesvalue(params, 'site_updated')
    set_timesvalue(params, 'site_uploaded')


# #### Auxiliary functions

def update_illust_urls(illust, params):
    update_results = []
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            illust_url = models.IllustUrl(illust_id=illust.id)
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
    illust = models.Illust(created=current_time, updated=current_time, requery=(current_time + datetime.timedelta(days=1)))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(illust, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_relationship_collections(illust, create_relationships, createparams)
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    append_relationship_collections(illust, append_relationships, createparams)
    update_site_data_from_parameters(illust.site_data, illust.id, illust.site_id, createparams)
    if 'illust_urls' in createparams:
        update_illust_urls(illust, createparams['illust_urls'])
    print("[%s]: created" % illust.shortlink)
    return illust


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


# ###### UPDATE

def update_illust_from_parameters(illust, updateparams):
    update_results = []
    set_timesvalues(updateparams)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(illust, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(update_relationship_collections(illust, update_relationships, updateparams))
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(append_relationship_collections(illust, append_relationships, updateparams))
    update_results.append(update_site_data_from_parameters(illust.site_data, illust.id, illust.site_id, updateparams))
    if 'illust_urls' in updateparams:
        update_results.append(update_illust_urls(illust, updateparams['illust_urls']))
    if any(update_results):
        print("[%s]: updated" % illust.shortlink)
        illust.updated = get_current_time()
        SESSION.commit()
    if 'requery' in updateparams:
        illust.requery = updateparams['requery']
        SESSION.commit()


def update_illust_from_source(illust, source):
    updateparams = source.get_illust_data(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag.name for tag in illust.tags if tag.name not in updateparams['tags']]
    update_illust_from_parameters(illust, updateparams)


# ###### Misc

def illust_delete_commentary(illust, description_id):
    retdata = {'error': False, 'descriptions': [commentary.to_json() for commentary in illust.commentaries]}
    remove_commentary = next((commentary for commentary in illust.commentaries if commentary.id == description_id), None)
    if remove_commentary is None:
        return set_error(retdata, "Commentary with description #%d does not exist on illust #%d." % (description_id, illust.id))
    illust.commentaries.remove(remove_commentary)
    SESSION.commit()
    retdata['item'] = illust.to_json()
    return retdata


# #### Query functions

def get_site_illust(site_illust_id, site_id):
    return models.Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()
