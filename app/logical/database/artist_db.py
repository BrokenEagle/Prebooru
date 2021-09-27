# APP/LOGICAL/DATABASE/ARTIST_DB.PY

import datetime

from ... import SESSION
from ..utility import get_current_time, set_error
from ...models import Artist, ArtistUrl, Label, Description
from .base_db import update_column_attributes, update_relationship_collections, append_relationship_collections, set_timesvalue


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('site_accounts', 'name', Label), ('names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = [('profiles', 'body', Description)]

CREATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'site_accounts', 'names', 'profiles']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'site_accounts', 'names', 'profiles']


# ## FUNCTIONS

# #### Helper functions

def set_all_site_accounts(params):
    if 'current_site_account' in params and params['current_site_account']:
        params['site_accounts'] = list(set(params['site_accounts'] + [params['current_site_account']]))


# #### DB functions

# ###### Create

def create_artist_from_parameters(createparams):
    current_time = get_current_time()
    set_timesvalue(createparams, 'site_created')
    set_all_site_accounts(createparams)
    artist = Artist(created=current_time, updated=current_time, requery=(current_time + datetime.timedelta(days=1)))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(artist, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_relationship_collections(artist, create_relationships, createparams)
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    append_relationship_collections(artist, append_relationships, createparams)
    if 'webpages' in createparams:
        update_artist_webpages(artist, createparams['webpages'])
    print("[%s]: created" % artist.shortlink)
    return artist


# ###### Update


def update_artist_from_parameters(artist, updateparams):
    update_results = []
    set_timesvalue(updateparams, 'site_created')
    set_all_site_accounts(updateparams)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(artist, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(update_relationship_collections(artist, update_relationships, updateparams))
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(append_relationship_collections(artist, append_relationships, updateparams))
    if 'webpages' in updateparams:
        update_results.append(update_artist_webpages(artist, updateparams['webpages']))
    if any(update_results):
        print("[%s]: updated" % artist.shortlink)
        artist.updated = get_current_time()
        SESSION.commit()
    if 'requery' in updateparams:
        artist.requery = updateparams['requery']
        SESSION.commit()


# #### Auxiliary functions

def update_artist_webpages(artist, params):
    existing_webpages = [webpage.url for webpage in artist.webpages]
    current_webpages = []
    is_dirty = False
    for url in params:
        is_active = url[0] != '-'
        if not is_active:
            url = url[1:]
        artist_url = next(filter(lambda x: x.url == url, artist.webpages), None)
        if artist_url is None:
            data = {
                'artist_id': artist.id,
                'url': url,
                'active': is_active,
            }
            artist_url = ArtistUrl(**data)
            SESSION.add(artist_url)
            is_dirty = True
        elif artist_url.active != is_active:
            artist_url.active = is_active
            is_dirty = True
        current_webpages.append(url)
    removed_webpages = set(existing_webpages).difference(current_webpages)
    for url in removed_webpages:
        # These will only be removable from the edit artist interface
        artist_url = next(filter(lambda x: x.url == url, artist.webpages))
        SESSION.delete(artist_url)
        is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


# ###### Misc

def artist_append_booru(artist, booru):
    artist.boorus.append(booru)
    artist.updated = get_current_time()
    SESSION.commit()


def artist_delete_profile(artist, description_id):
    retdata = {'error': False, 'descriptions': [profile.to_json() for profile in artist.profiles]}
    remove_profile = next((profile for profile in artist.profiles if profile.id == description_id), None)
    if remove_profile is None:
        return set_error(retdata, "Profile with description #%d does not exist on artist #%d." % (description_id, artist.id))
    artist.profiles.remove(remove_profile)
    SESSION.commit()
    retdata['item'] = artist.to_json()
    return retdata


# #### Query functions

def get_site_artist(site_artist_id, site_id):
    return Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
