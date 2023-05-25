# APP/LOGICAL/DATABASE/MEDIA_ASSET_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import MediaAsset
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['md5', 'width', 'height', 'size', 'pixel_md5', 'duration', 'audio', 'file_ext']
CREATE_ALLOWED_ATTRIBUTES = ['md5', 'width', 'height', 'size', 'pixel_md5', 'duration', 'audio', 'file_ext']
UPDATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'size', 'pixel_md5', 'duration', 'audio', 'file_ext']


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_media_asset_from_parameters(createparams):
    media_asset = MediaAsset()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(media_asset, update_columns, createparams, commit=False)
    print("[%s]: created" % media_asset.shortlink)
    return media_asset


# ###### Update

def update_media_asset_from_parameters(media_asset, updateparams):
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    # Only allow NULL columns to be set
    update_columns = [col for col in update_columns if getattr(media_asset, col) is None]
    if update_column_attributes(media_asset, update_columns, updateparams, commit=False):
        print("[%s]: updated" % media_asset.shortlink)
    return media_asset


def update_media_asset_location(media_asset, location):
    media_asset.location_id = MediaAsset.location_enum.by_name(location).id
    SESSION.flush()


# ###### Query

def get_media_asset_by_md5(md5):
    return MediaAsset.query.filter_by(md5=md5).one_or_none()


# ###### Misc

def create_or_update_media_asset_from_parameters(params):
    media_asset = MediaAsset.query.filter_by(md5=params['md5']).first()
    if media_asset is None:
        return create_media_asset_from_parameters(params)
    #return update_media_asset_from_parameters(media_asset, params)
