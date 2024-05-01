# APP/LOGICAL/DATABASE/MEDIA_ASSET_DB.PY

# ## LOCAL IMPORTS
from ...models import MediaAsset
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['location_id']
NULL_WRITABLE_ATTRIBUTES = ['md5', 'width', 'height', 'size', 'pixel_md5', 'duration', 'audio', 'file_ext']


# ## FUNCTIONS

# #### Create

def create_media_asset_from_parameters(createparams, commit=True):
    return set_media_asset_from_parameters(MediaAsset(), createparams, commit, 'created')


# #### Update

def update_media_asset_from_parameters(media_asset, updateparams, commit=True):
    return set_media_asset_from_parameters(media_asset, updateparams, commit, 'updated')


# #### Set

def set_media_asset_from_parameters(media_asset, setparams, commit, action):
    if 'location' in params:
        setparams['location_id'] = MediaAsset.location_enum.by_name(setparams['location']).id
    if set_column_attributes(media_asset, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        commit_or_flush(commit, safe=True)
        print("[%s]: %s" % (media_asset.shortlink, action))
    return media_asset


# #### Query

def get_media_asset_by_md5(md5):
    return MediaAsset.query.filter_by(md5=md5).one_or_none()


# #### Misc

def create_or_update_media_asset_from_parameters(params):
    media_asset = MediaAsset.query.filter_by(md5=params['md5']).first()
    if media_asset is None:
        return create_media_asset_from_parameters(params)
    return update_media_asset_from_parameters(media_asset, params)
