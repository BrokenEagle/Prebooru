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
        SubscriptionElementKeep, UploadStatus, PoolElementType, TagType,\
        Tag, SiteTag, UserTag, Label, Description,\
        Illust, IllustTags, IllustTitles, IllustCommentaries, AdditionalCommentaries, IllustUrl,\
        ArtistUrl, Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles,\
        Booru, BooruNames, BooruArtists, Error, Post,\
        PostTags, Upload, Notation, Pool, PoolElement, PoolPost,\
        PoolIllust, PoolNotation, Subscription, SubscriptionElement,\
        ImageHash, SimilarityMatch, ApiData,\
        Archive, ArchivePost,\
        Download, DownloadElement, DownloadUrl,\
        Download, DownloadElement, DownloadUrl, DownloadStatus, DownloadElementStatus,\
        MediaFile,\
        ServerInfo,\
        JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus

    # #### Enum data
    from .model_enums import SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus,\
        SubscriptionElementStatus, SubscriptionElementKeep, UploadStatus, PoolElementType,\
        TagType, DownloadStatus, DownloadElementStatus

    # #### Site data
    from .tag import Tag, SiteTag, UserTag
    from .label import Label
    from .description import Description
    from .illust_url import IllustUrl
    from .illust import Illust, IllustTags, IllustTitles, IllustCommentaries, AdditionalCommentaries
    from .artist_url import ArtistUrl
    from .artist import Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles
    from .booru import Booru, BooruNames, BooruArtists

    # #### Local data
    from .error import Error
    from .post import Post, PostTags
    from .download import Download
    from .download_element import DownloadElement
    from .download_url import DownloadUrl
    from .upload import Upload
    from .notation import Notation
    from .pool import Pool
    from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation
    from .subscription import Subscription
    from .subscription_element import SubscriptionElement

    # #### Similarity data
    from .image_hash import ImageHash
    from .similarity_match import SimilarityMatch

    # #### Cache data
    from .api_data import ApiData
    from .archive import Archive
    from .archive_post import ArchivePost
    from .media_file import MediaFile

    # #### Server data

    from .server_info import ServerInfo

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
            SubscriptionElementKeep, UploadStatus, PoolElementType, TagType,
            Tag, SiteTag, UserTag, Label, Description,
            Illust, IllustTags, IllustTitles, IllustCommentaries, AdditionalCommentaries, IllustUrl,
            ArtistUrl, Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles,
            Booru, BooruNames, BooruArtists, Error, Post,
            PostTags, Upload, Notation, Pool, PoolElement, PoolPost,
            PoolIllust, PoolNotation, Subscription, SubscriptionElement,
            ImageHash, SimilarityMatch, ApiData,
            Archive, ArchivePost,
            Download, DownloadElement, DownloadUrl,
            Download, DownloadElement, DownloadUrl, DownloadStatus, DownloadElementStatus,
            MediaFile,
            ServerInfo,
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


def enums_need_upgrade():
    models =\
        [
            SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus, SubscriptionElementStatus,
            SubscriptionElementKeep, UploadStatus, PoolElementType, TagType,
        ]
    return any(model.is_empty or model.mapping.needs_upgrade for model in models)
