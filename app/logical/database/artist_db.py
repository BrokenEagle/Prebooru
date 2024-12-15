# APP/LOGICAL/DATABASE/ARTIST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import not_

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.uprint import buffered_print

# ## LOCAL IMPORTS
from ...models import Artist, ArtistUrl, Booru, Label, Description
from ..utility import set_error
from .base_db import set_column_attributes, set_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes, add_record, delete_record, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'primary']
UPDATE_SCALAR_RELATIONSHIPS = [('_site_accounts', 'name', Label), ('_names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = [('_profiles', 'body', Description)]
ALL_SCALAR_RELATIONSHIPS = UPDATE_SCALAR_RELATIONSHIPS + APPEND_SCALAR_RELATIONSHIPS
ASSOCIATION_ATTRIBUTES = ['site_accounts', 'names', 'profiles']
NORMALIZED_ASSOCIATE_ATTRIBUTES = ['_' + key for key in ASSOCIATION_ATTRIBUTES]

CREATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'primary',
                             '_site_accounts', '_names', '_profiles']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'primary',
                             '_site_accounts', '_names', '_profiles']

ANY_WRITABLE_COLUMNS = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'primary']
NULL_WRITABLE_ATTRIBUTES = []

BOORU_SUBQUERY = Artist.query\
    .join(Booru, Artist.boorus)\
    .filter(Booru.deleted.is_(False), Booru.danbooru_id.is_not(None))\
    .with_entities(Artist.id)
BOORU_SUBCLAUSE = Artist.id.in_(BOORU_SUBQUERY)


# ## FUNCTIONS

# #### DB functions

# ###### Create

def create_artist_from_parameters(createparams):
    artist = Artist(primary=True)
    if 'site' in createparams:
        createparams['site_id'] = Artist.site_enum.by_name(createparams['site']).id
    set_timesvalue(createparams, 'site_created')
    _set_all_site_accounts(createparams, artist)
    set_column_attributes(artist, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams, safe=True)
    _set_relations(artist, createparams)
    _set_artist_webpages(artist, createparams)
    save_record(artist, 'created', safe=True)
    return artist


def create_artist_from_json(data):
    artist = Artist.loads(data)
    add_record(artist)
    save_record(artist, 'created')
    return artist


# ###### Update

def update_artist_from_parameters(artist, updateparams):
    if 'site' in updateparams:
        updateparams['site_id'] = Artist.site_enum.by_name(updateparams['site']).id
    set_timesvalue(updateparams, 'site_created')
    _set_all_site_accounts(updateparams, artist)
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    col_result = set_column_attributes(artist, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, updateparams, safe=True)
    rel_result = _set_relations(artist, updateparams)
    web_result = _set_artist_webpages(artist, updateparams)
    if col_result or rel_result or web_result:
        save_record(artist, 'updated', safe=True)


def recreate_artist_relations(artist, updateparams):
    rel_result = _set_relations(artist, updateparams)
    web_result = _set_artist_webpages(artist, updateparams)
    if rel_result or web_result:
        artist.updated = get_current_time()
        commit_session()


def inactivate_artist(artist):
    artist.active = False
    commit_session()


# ###### Delete

def delete_artist(artist):
    from ..records.illust_rec import archive_illust_for_deletion
    for illust in artist.illusts:
        archive_illust_for_deletion(illust)
    delete_record(artist)
    commit_session()


# ###### Misc

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


def artist_delete_profile(artist, description_id):
    retdata = {'error': False, 'descriptions': [profile.to_json() for profile in artist._profiles]}
    remove_profile = next((profile for profile in artist._profiles if profile.id == description_id), None)
    if remove_profile is None:
        msg = "Profile with description #%d does not exist on artist #%d." % (description_id, artist.id)
        return set_error(retdata, msg)
    artist._profiles.remove(remove_profile)
    commit_session()
    retdata['item'] = artist.to_json()
    return retdata


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


def _set_relations(artist, setparams):
    if isinstance(setparams.get('profiles'), str):
        setparams['_profiles_append'] = setparams['profiles'] if len(setparams['profiles']) else None
        setparams['profiles'] = None
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    set_rel_result = set_relationship_collections(artist, UPDATE_SCALAR_RELATIONSHIPS, setparams)
    append_rel_result = append_relationship_collections(artist, APPEND_SCALAR_RELATIONSHIPS, setparams)
    return any([set_rel_result, append_rel_result])


def _set_artist_webpages(artist, params):
    if 'webpages' not in params:
        return False
    printer = buffered_print('set_artist_webpages', safe=True, header=False)
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
            printer("Adding artist url [%s]:" % artist.shortlink, url, is_active)
            artist_url = ArtistUrl(**data)
            add_record(artist_url)
            update_results = True
        elif artist_url.active != is_active:
            printer("Updating %s (%s):" % (artist_url.shortlink, artist_url.url), artist_url.active, is_active)
            artist_url.active = is_active
            update_results = True
        current_webpages.append(url)
    removed_webpages = set(existing_webpages).difference(current_webpages)
    for url in removed_webpages:
        # These will only be removable via the artist urls controller
        printer("Inactivating %s (%s):" % (artist_url.shortlink, artist_url.url))
        artist_url = next(filter(lambda x: x.url == url, artist.webpages))
        artist_url.active = False
        update_results = True
    if update_results:
        printer.print()
        flush_session()
    return update_results
