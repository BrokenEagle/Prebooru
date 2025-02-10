# APP/LOGICAL/DATABASE/ARCHIVE_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ...models import Archive, ArchivePost, ArchiveIllust, ArchiveArtist, ArchiveBooru
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['expires']
NULL_WRITABLE_ATTRIBUTES = ['type_name']


# ## FUNCTIONS

# #### Create

def create_archive_from_parameters(createparams, commit=True):
    return set_archive_from_parameters(Archive(), createparams, 'created', commit)


# #### Update

def update_archive_from_parameters(archive, updateparams, commit=True):
    return set_archive_from_parameters(archive, updateparams, 'updated', commit)


# #### Set

def set_archive_from_parameters(archive, setparams, action, commit):
    if 'expires' in setparams:
        set_timesvalue(setparams, 'expires')
    elif 'days' in setparams:
        setparams['expires'] = days_from_now(setparams['days']) if setparams['days'] is not None else None
    if set_column_attributes(archive, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive, action, commit=commit)
    return archive


# #### Query functions

def get_archive_by_post_md5(md5):
    return Archive.query.join(ArchivePost).filter(ArchivePost.md5 == md5).one_or_none()


def get_archives_by_post_md5s(data_keys):
    archive_posts = []
    for i in range(0, len(data_keys), 100):
        sublist = data_keys[i: i + 100]
        archive_posts += Archive.query.join(ArchivePost).filter(ArchivePost.md5.in_(sublist)).all()
    return archive_posts


def get_archive_by_illust_site(site_id, site_illust_id):
    return Archive.query.join(ArchiveIllust).filter(ArchiveIllust.site_id == site_id,
                                                    ArchiveIllust.site_illust_id == site_illust_id)\
                                            .one_or_none()


def get_archive_by_artist_site(site_id, site_artist_id):
    return Archive.query.join(ArchiveArtist).filter(ArchiveArtist.site_id == site_id,
                                                    ArchiveArtist.site_artist_id == site_artist_id)\
                                            .one_or_none()


def get_archive_by_booru_name(name):
    return Archive.query.join(ArchiveBooru).filter(ArchiveBooru.name == name).one_or_none()


def expired_archive_count():
    return Archive.query.filter(Archive.expires < get_current_time()).get_count()
