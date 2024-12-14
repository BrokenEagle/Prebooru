# APP/LOGICAL/DATABASE/ARTIST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import not_

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Artist, ArtistUrl, Booru, Label, Description
from ..utility import set_error
from .base_db import update_column_attributes, update_relationship_collections, append_relationship_collections,\
    set_timesvalue, set_association_attributes, add_record, delete_record, save_record, commit_session


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

BOORU_SUBQUERY = Artist.query\
    .join(Booru, Artist.boorus)\
    .filter(Booru.deleted.is_(False), Booru.danbooru_id.is_not(None))\
    .with_entities(Artist.id)
BOORU_SUBCLAUSE = Artist.id.in_(BOORU_SUBQUERY)


# ## FUNCTIONS

# #### Helper functions

def set_all_site_accounts(params, artist):
    if 'current_site_account' in params and params['current_site_account']:
        artist_accounts = list(artist.site_accounts) if artist is not None else []
        params['site_accounts'] = params.get('site_accounts', artist_accounts)
        params['site_accounts'] = list(set(params['site_accounts'] + [params['current_site_account']]))


# #### DB functions

# ###### Create

def create_artist_from_parameters(createparams):
    if type(createparams.get('profiles')) is str:
        createparams['profiles'] = [createparams['profiles']]
    if 'site' in createparams:
        createparams['site_id'] = Artist.site_enum.by_name(createparams['site']).id
    createparams['primary'] = createparams['primary'] if 'primary' in createparams else True
    current_time = get_current_time()
    set_timesvalue(createparams, 'site_created')
    set_all_site_accounts(createparams, None)
    artist = Artist(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(artist, update_columns, createparams)
    _update_relations(artist, createparams, overwrite=True, create=True)
    save_record(artist, 'created')
    return artist


def create_artist_from_json(data):
    artist = Artist.loads(data)
    add_record(artist)
    save_record(artist, 'created')
    return artist


# ###### Update

def update_artist_from_parameters(artist, updateparams):
    update_results = []
    if 'site' in updateparams:
        updateparams['site_id'] = Artist.site_enum.by_name(updateparams['site']).id
    set_timesvalue(updateparams, 'site_created')
    set_all_site_accounts(updateparams, artist)
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(artist, update_columns, updateparams))
    update_results.append(_update_relations(artist, updateparams, overwrite=False, create=False))
    if any(update_results):
        artist.updated = get_current_time()
        save_record(artist, 'updated')


def recreate_artist_relations(artist, updateparams):
    _update_relations(artist, updateparams, overwrite=True, create=False)


def inactivate_artist(artist):
    artist.active = False
    commit_session()


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
            add_record(artist_url)
            is_dirty = True
        elif artist_url.active != is_active:
            artist_url.active = is_active
            is_dirty = True
        current_webpages.append(url)
    removed_webpages = set(existing_webpages).difference(current_webpages)
    for url in removed_webpages:
        # These will only be removable from the edit artist interface
        artist_url = next(filter(lambda x: x.url == url, artist.webpages))
        delete_record(artist_url)
        is_dirty = True
    if is_dirty:
        commit_session()
    return is_dirty


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

def _update_relations(artist, updateparams, overwrite=None, create=None):
    update_results = []
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    allowed_attributes = CREATE_ALLOWED_ATTRIBUTES if create else UPDATE_ALLOWED_ATTRIBUTES
    settable_keylist = set(updateparams.keys()).intersection(allowed_attributes)
    relationship_list = ALL_SCALAR_RELATIONSHIPS if overwrite else UPDATE_SCALAR_RELATIONSHIPS
    update_relationships = [rel for rel in relationship_list if rel[0] in settable_keylist]
    update_results.append(update_relationship_collections(artist, update_relationships, updateparams))
    if not overwrite:
        append_relationships = [rel for rel in APPEND_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
        update_results.append(append_relationship_collections(artist, append_relationships, updateparams))
    if 'webpages' in updateparams:
        update_results.append(update_artist_webpages(artist, updateparams['webpages']))
    return any(update_results)
