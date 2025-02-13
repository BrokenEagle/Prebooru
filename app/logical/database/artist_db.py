# APP/LOGICAL/DATABASE/ARTIST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import not_, tuple_

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.data import swap_key_value

# ## LOCAL IMPORTS
from ...models import Artist, Booru
from .base_db import set_column_attributes, set_version_relations, set_timesvalue,\
    save_record, commit_session, flush_session
from .artist_url_db import create_artist_url_from_parameters, update_artist_url_from_parameters

# ## GLOBAL VARIABLES

VERSION_RELATIONSHIPS = [('site_account_value', 'site_account_values'), ('name_value', 'name_values'),
                         ('profile_body', 'profile_bodies')]

ANY_WRITABLE_COLUMNS = ['site_name', 'site_artist_id', 'site_created', 'active', 'primary']
NULL_WRITABLE_ATTRIBUTES = ['site_account_value', 'name_value', 'profile_body', 'created', 'updated']

BOORU_SUBQUERY = Artist.query\
    .join(Booru, Artist.boorus)\
    .filter(Booru.deleted.is_(False), Booru.danbooru_id.is_not(None))\
    .with_entities(Artist.id)
BOORU_SUBCLAUSE = Artist.id.in_(BOORU_SUBQUERY)


# ## FUNCTIONS

# #### Create

def create_artist_from_parameters(createparams, commit=True):
    createparams.setdefault('active', True)
    createparams.setdefault('primary', True)
    set_timesvalue(createparams, 'created')
    set_timesvalue(createparams, 'updated')
    return set_artist_from_parameters(Artist(), createparams, 'created', commit, True)


# #### Update

def update_artist_from_parameters(artist, updateparams, commit=True, update=True):
    return set_artist_from_parameters(artist, updateparams, 'updated', commit, update)


def update_artist_from_parameters_standard(artist, updateparams):
    """Set parameters that are only removable through direct user interaction before updating."""
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        if 'webpages' in updateparams:
            updateparams['webpages'] += ['-' + w.url for w in artist.webpages if w.url not in updateparams['webpages']]
    else:
        # When deactivating automatically, don't allow any other parameters to be set
        updateparams = {'active': False}
    update_artist_from_parameters(artist, updateparams, commit=True, update=False)


# #### Set

def set_artist_from_parameters(artist, setparams, action, commit, update):
    swap_key_value(setparams, 'site_account', 'site_account_value')
    swap_key_value(setparams, 'name', 'name_value')
    swap_key_value(setparams, 'profile', 'profile_body')
    set_timesvalue(setparams, 'site_created')
    col_result = set_column_attributes(artist, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    ver_result = set_version_relations(artist, VERSION_RELATIONSHIPS, setparams, update=update)\
        if action == 'updated' else False
    web_result = _set_artist_webpages(artist, setparams, update)
    if col_result or ver_result or web_result:
        save_record(artist, action, commit=commit, safe=True)
    return artist


# #### Misc

def get_blank_artist():
    artist = Artist.query.filter(Artist.site_value == 'custom', Artist.site_artist_id == 1).one_or_none()
    if not artist:
        createparams = {
            'site_name': 'custom',
            'site_artist_id': 1,
            'site_account': 'Prebooru',
            'active': True,
        }
        artist = create_artist_from_parameters(createparams)
    return artist


def artist_append_booru(artist, booru):
    artist.boorus.append(booru)
    artist.updated = get_current_time()
    commit_session()


# #### Query functions

def get_site_artist(site_artist_id, site):
    q = Artist.query
    if isinstance(site, int):
        q = q.filter(Artist.site_id == site)
    elif isinstance(site, str):
        q = q.filter(Artist.site_value == site)
    return q.filter(Artist.site_artist_id == site_artist_id).one_or_none()


def get_site_artists(artist_keys):
    """Expected key format is [site_id, site_artist_id]."""
    for key in artist_keys:
        # Convert site_name to site_id
        if isinstance(key[0], str):
            key[0] = Artist.site_enum.to_id(key[0])
    return Artist.query.filter(tuple_(Artist.site_id, Artist.site_artist_id).in_(artist_keys)).all()


def get_artists_without_boorus_page(limit):
    return Artist.query.filter(Artist.primary.is_(True), not_(BOORU_SUBCLAUSE)).limit_paginate(per_page=limit)


# #### Private functions

def _set_artist_webpages(artist, params, update):
    if 'webpages' not in params:
        return False
    update_results = False
    existing_webpages = [webpage.url for webpage in artist.webpages]
    current_webpages = []
    for url in params['webpages']:
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
            create_artist_url_from_parameters(data)
            update_results = True
        elif artist_url.active != is_active:
            update_artist_url_from_parameters(artist_url, {'active': is_active})
            update_results = True
        current_webpages.append(url)
    removed_webpages = set(existing_webpages).difference(current_webpages)
    for url in removed_webpages:
        # These will only be removable via the artist urls controller
        artist_url = next(filter(lambda x: x.url == url, artist.webpages))
        update_artist_url_from_parameters(artist_url, {'active': False})
        update_results = True
    if update_results:
        if update:
            artist.updated = get_current_time()
        flush_session()
    return update_results
