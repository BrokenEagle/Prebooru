# APP/MODELS/__INIT__.PY

"""Defines the columns, relationships, properties, and methods on the models."""

# ## PYTHON IMPORTS
from types import ModuleType

# ## EXTERNAL IMPORTS
import sqlalchemy

# ## LOCAL IMPORTS
from .. import DB

# ## COLLATION IMPORTS

# #### Site data
from .tag import Tag, SiteTag, UserTag  # noqa: F401
from .label import Label  # noqa: F401
from .description import Description  # noqa: F401
from .site_data import SiteData, PixivData, TwitterData  # noqa: F401
from .illust_url import IllustUrl  # noqa: F401
from .illust import Illust, IllustTags, IllustCommentaries, IllustNotations  # noqa: F401
from .artist_url import ArtistUrl  # noqa: F401
from .artist import Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles, ArtistNotations  # noqa: F401
from .booru import Booru, BooruNames, BooruArtists  # noqa: F401

# #### Local data
from .error import Error  # noqa: F401
from .post import Post, PostIllustUrls, PostErrors, PostNotations, PostTags  # noqa: F401
from .upload import Upload, UploadUrls, UploadErrors  # noqa: F401
from .upload_element import UploadElement, UploadElementErrors  # noqa: F401
from .upload_url import UploadUrl  # noqa: F401
from .notation import Notation  # noqa: F401
from .pool import Pool  # noqa: F401
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation  # noqa: F401
from .subscription import Subscription, SubscriptionErrors  # noqa: F401
from .subscription_element import SubscriptionElement, SubscriptionElementErrors  # noqa: F401

# #### Similarity data
from .image_hash import ImageHash  # noqa: F401
from .similarity_match import SimilarityMatch  # noqa: F401

# #### Cache data
from .api_data import ApiData  # noqa: F401
from .archive import Archive  # noqa: F401
from .media_file import MediaFile  # noqa: F401
from .domain import Domain  # noqa: F401

# #### Server data

from .server_info import ServerInfo

# #### Job data
from .jobs import JobInfo, JobEnable, JobLock, JobManual, JobTime, JobStatus


# ## GLOBAL VARIABLES

NONCE = None
TABLES = {}


# ## FUNCTIONS

def initialize():

    def _is_initialize_module(name, value):
        return type(value) is ModuleType and name != '__builtins__' and hasattr(value, 'initialize')

    modules = [value for (name, value) in globals().items() if _is_initialize_module(name, value)]
    for mod in modules:
        mod.initialize()

    models =\
        [
            Tag, SiteTag, UserTag, Label, Description, SiteData, PixivData, TwitterData, IllustUrl, Illust, IllustTags,
            IllustCommentaries, IllustNotations, ArtistUrl, Artist, ArtistNames, ArtistSiteAccounts, ArtistProfiles,
            ArtistNotations, Booru, BooruNames, BooruArtists, Error, Post, PostIllustUrls, PostErrors, PostNotations,
            PostTags, UploadUrl, Upload, UploadUrls, UploadErrors, Notation, Pool, PoolElement, PoolPost,
            PoolIllust, PoolNotation, Subscription, SubscriptionErrors, SubscriptionElement,
            SubscriptionElementErrors, ImageHash, SimilarityMatch, ApiData, Archive,
            UploadElement, UploadElementErrors,
            MediaFile, Domain,
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


# ## INITIALIZATION

initialize()
