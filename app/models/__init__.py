# APP/MODELS/__INIT__.PY

"""Defines the columns, relationships, properties, and methods on the models."""

# ## PYTHON IMPORTS
from types import ModuleType

# ## EXTERNAL IMPORTS
import sqlalchemy

# ## LOCAL IMPORTS
from .. import DB


# ## GLOBAL VARIABLES

NONCE = None
TABLES = {}


# ## FUNCTIONS

def load_all():
    global\
        SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus, SubscriptionElementStatus,\
        SubscriptionElementKeep, UploadStatus, UploadElementStatus, PoolElementType, SiteDataType, TagType,\
        Tag, SiteTag, UserTag, Label, Description, SiteData, PixivData, TwitterData, IllustUrl, Illust, IllustTags,\
        IllustCommentaries, IllustNotations, ArtistUrl, Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles,\
        ArtistNotations, Booru, BooruNames, BooruArtists, Error, Post, PostIllustUrls, PostErrors, PostNotations,\
        PostTags, UploadUrl, Upload, UploadUrls, UploadErrors, Notation, Pool, PoolElement, PoolPost,\
        PoolIllust, PoolNotation, Subscription, SubscriptionErrors, SubscriptionElement,\
        SubscriptionElementErrors, ImageHash, SimilarityMatch, ApiData, Archive,\
        UploadElement, UploadElementErrors,\
        MediaFile, Domain,\
        ServerInfo, Version,\
        JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus

    # #### Enum data
    from .model_enums import SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus,\
        SubscriptionElementStatus, SubscriptionElementKeep, UploadStatus, UploadElementStatus, PoolElementType,\
        SiteDataType, TagType

    # #### Site data
    from .tag import Tag, SiteTag, UserTag
    from .label import Label
    from .description import Description
    from .site_data import SiteData, PixivData, TwitterData
    from .illust_url import IllustUrl
    from .illust import Illust, IllustTags, IllustCommentaries, IllustNotations
    from .artist_url import ArtistUrl
    from .artist import Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles, ArtistNotations
    from .booru import Booru, BooruNames, BooruArtists

    # #### Local data
    from .error import Error
    from .post import Post, PostIllustUrls, PostErrors, PostNotations, PostTags
    from .upload import Upload, UploadUrls, UploadErrors
    from .upload_element import UploadElement, UploadElementErrors
    from .upload_url import UploadUrl
    from .notation import Notation
    from .pool import Pool
    from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation
    from .subscription import Subscription, SubscriptionErrors
    from .subscription_element import SubscriptionElement, SubscriptionElementErrors

    # #### Similarity data
    from .image_hash import ImageHash
    from .similarity_match import SimilarityMatch

    # #### Cache data
    from .api_data import ApiData
    from .archive import Archive
    from .media_file import MediaFile
    from .domain import Domain

    # #### Server data

    from .server_info import ServerInfo
    from .version import Version

    # #### Job data
    from .jobs import JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus


def initialize():

    def _is_initialize_module(name, value):
        return type(value) is ModuleType and name != '__builtins__' and hasattr(value, 'initialize')

    load_all()

    modules = [value for (name, value) in globals().items() if _is_initialize_module(name, value)]
    for mod in modules:
        mod.initialize()

    models =\
        [
            SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus, SubscriptionElementStatus,
            SubscriptionElementKeep, UploadStatus, UploadElementStatus, PoolElementType, SiteDataType, TagType,
            Tag, SiteTag, UserTag, Label, Description, SiteData, PixivData, TwitterData, IllustUrl, Illust, IllustTags,
            IllustCommentaries, IllustNotations, ArtistUrl, Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles,
            ArtistNotations, Booru, BooruNames, BooruArtists, Error, Post, PostIllustUrls, PostErrors, PostNotations,
            PostTags, UploadUrl, Upload, UploadUrls, UploadErrors, Notation, Pool, PoolElement, PoolPost,
            PoolIllust, PoolNotation, Subscription, SubscriptionErrors, SubscriptionElement,
            SubscriptionElementErrors, ImageHash, SimilarityMatch, ApiData, Archive,
            UploadElement, UploadElementErrors,
            MediaFile, Domain,
            ServerInfo, Version,
            JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus,
        ]
    for model in models:
        key = model._model_name()
        TABLES[key] = model
        if isinstance(model, sqlalchemy.Table):
            if not hasattr(model, '_secondary_table'):
                model._secondary_table = False
        elif issubclass(model, DB.Model):
            model.__table__._secondary_table = False
