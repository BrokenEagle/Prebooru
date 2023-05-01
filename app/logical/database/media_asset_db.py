# APP/LOGICAL/DATABASE/MEDIA_ASSET_DB.PY

# ## LOCAL IMPORTS
from ...models import MediaAsset, Post, MediaFile, Archive, SubscriptionElement, UploadElement
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

MODELS_WITH_MEDIA = Post.query.with_entities(Post.media_asset_id)\
                        .union(MediaFile.query.with_entities(MediaFile.media_asset_id))\
                        .union(Archive.query.filter(Archive.media_asset_id.is_not(None))
                                            .with_entities(Archive.media_asset_id))

ALL_MODELS = MODELS_WITH_MEDIA\
    .union(
        SubscriptionElement.query
                           .filter(SubscriptionElement.media_asset_id.is_not(None))
                           .with_entities(SubscriptionElement.media_asset_id)
    )\
    .union(
        UploadElement.query
                     .filter(UploadElement.media_asset_id.is_not(None))
                     .with_entities(UploadElement.media_asset_id)
    )

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
    if 'location' in setparams:
        setparams['location_id'] = MediaAsset.location_enum.by_name(setparams['location']).id
    if set_column_attributes(media_asset, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        commit_or_flush(commit, safe=True)
        print("[%s]: %s" % (media_asset.shortlink, action))
    return media_asset


# #### Delete

def delete_unattached_media_assets():
    total = MediaAsset.query.filter(MediaAsset.id.not_in(ALL_MODELS)).delete()
    commit_or_flush(True)
    return total


# #### Query

def get_media_asset_by_md5(md5):
    return MediaAsset.query.filter_by(md5=md5).one_or_none()


def media_assets_without_media_models_query():
    return MediaAsset.query.enum_join(MediaAsset.location_enum)\
                           .filter(MediaAsset.id.not_in(MODELS_WITH_MEDIA),
                                   MediaAsset.location_filter('id', 'is_not', None))


# #### Misc

def create_or_update_media_asset_from_parameters(params):
    media_asset = get_media_asset_by_md5(params['md5'])
    if media_asset is None:
        return create_media_asset_from_parameters(params)
    return update_media_asset_from_parameters(media_asset, params)
