# APP/LOGICAL/DATABASE/ARTIST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import not_

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Artist, Booru, Label, Description
from .base_db import set_column_attributes, set_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes, add_record, save_record, commit_session, flush_session
from .artist_url_db import create_artist_url_from_parameters, update_artist_url_from_parameters

# ## GLOBAL VARIABLES

UPDATE_SCALAR_RELATIONSHIPS = [('_site_accounts', 'name', Label), ('_names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = [('_profiles', 'body', Description)]
ASSOCIATION_ATTRIBUTES = ['site_accounts', 'names', 'profiles']

ANY_WRITABLE_COLUMNS = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'primary']
NULL_WRITABLE_ATTRIBUTES = []

BOORU_SUBQUERY = Artist.query\
    .join(Booru, Artist.boorus)\
    .filter(Booru.deleted.is_(False), Booru.danbooru_id.is_not(None))\
    .with_entities(Artist.id)
BOORU_SUBCLAUSE = Artist.id.in_(BOORU_SUBQUERY)


# ## FUNCTIONS

# #### Create

def create_artist_from_parameters(createparams, commit=True):
    artist = Artist(primary=True)
    return set_artist_from_parameters(artist, createparams, 'created', commit, True)


def create_artist_from_json(data):
    artist = Artist.loads(data)
    add_record(artist)
    save_record(artist, 'created')
    return artist


# #### Update

def update_artist_from_parameters(artist, updateparams, commit=True, update=True):
    return set_artist_from_parameters(artist, updateparams, 'updated', commit, update)


def recreate_artist_relations(artist, updateparams):
    rel_result = _set_relations(artist, updateparams, False)
    web_result = _set_artist_webpages(artist, updateparams, False)
    if rel_result or web_result:
        commit_session()


# #### Set

def set_artist_from_parameters(artist, setparams, action, commit, update):
    if 'site' in setparams:
        setparams['site_id'] = Artist.site_enum.by_name(setparams['site']).id
    set_timesvalue(setparams, 'site_created')
    _set_all_site_accounts(setparams, artist)
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    col_result = set_column_attributes(artist, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    rel_result = _set_relations(artist, setparams, update)
    web_result = _set_artist_webpages(artist, setparams, update)
    if col_result or rel_result or web_result:
        save_record(artist, action, commit=commit, safe=True)
    return artist


# #### Misc

def get_blank_artist():
    artist = Artist.query.enum_join(Artist.site_enum)\
                         .filter(Artist.site_filter('name', '__eq__', 'custom'),
                                 Artist.site_artist_id == 1)\
                         .one_or_none()
    if not artist:
        createparams = {
            'site': 0,
            'site_artist_id': 1,
            'current_site_account': 'Prebooru',
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
    if isinstance(site, int):
        enum_filter = Artist.site_filter('id', '__eq__', site)
    elif isinstance(site, str):
        enum_filter = Artist.site_filter('name', '__eq__', site)
    return Artist.query.enum_join(Artist.site_enum)\
                       .filter(enum_filter, Artist.site_artist_id == site_artist_id)\
                       .one_or_none()


def get_artists_without_boorus_page(limit):
    return Artist.query.filter(Artist.primary.is_(True), not_(BOORU_SUBCLAUSE)).limit_paginate(per_page=limit)


# #### Private functions

def _set_all_site_accounts(params, artist):
    if isinstance(params.get('current_site_account'), str):
        accounts = set(params.get('site_accounts', list(artist.site_accounts)) + [params['current_site_account']])
        params['site_accounts'] = list(accounts)


def _set_relations(artist, setparams, update):
    if isinstance(setparams.get('profiles'), str):
        setparams['_profiles_append'] = setparams['profiles'] if len(setparams['profiles']) else None
        setparams['profiles'] = None
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    set_rel_result = set_relationship_collections(artist, UPDATE_SCALAR_RELATIONSHIPS, setparams, update=update)
    append_rel_result = append_relationship_collections(artist, APPEND_SCALAR_RELATIONSHIPS, setparams, update=update)
    return any([set_rel_result, append_rel_result])


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
