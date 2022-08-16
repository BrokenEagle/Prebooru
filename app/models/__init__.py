# APP/MODELS/__INIT__.PY

"""Defines the columns, relationships, properties, and methods on the models."""

# ## PYTHON IMPORTS
from types import ModuleType


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
from .upload_url import UploadUrl  # noqa: F401
from .upload import Upload, UploadUrls, UploadErrors, UploadPosts  # noqa: F401
from .notation import Notation  # noqa: F401
from .pool import Pool  # noqa: F401
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation  # noqa: F401
from .subscription_pool import SubscriptionPool, SubscriptionPoolErrors  # noqa: F401
from .subscription_pool_element import SubscriptionPoolElement, SubscriptionPoolElementErrors  # noqa: F401

# #### Similarity data
from .similarity_data import SimilarityData  # noqa: F401
from .similarity_pool import SimilarityPool  # noqa: F401
from .similarity_pool_element import SimilarityPoolElement  # noqa: F401

# #### Cache data
from .api_data import ApiData  # noqa: F401
from .archive import ArchiveData  # noqa: F401
from .media_file import MediaFile  # noqa: F401
from .domain import Domain  # noqa: F401


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
            PostTags, UploadUrl, Upload, UploadUrls, UploadErrors, UploadPosts, Notation, Pool, PoolElement, PoolPost,
            PoolIllust, PoolNotation, SubscriptionPool, SubscriptionPoolErrors, SubscriptionPoolElement,
            SubscriptionPoolElementErrors, SimilarityData, SimilarityPool, SimilarityPoolElement, ApiData, ArchiveData,
            MediaFile, Domain,
        ]
    for model in models:
        if hasattr(model, '__table__'):
            key = model.__table__.name
        elif hasattr(model, 'name'):
            key = model.name
        else:
            raise Exception("Unrecognized model type: %s" % str(model))
        TABLES[key] = model


# ## INITIALIZATION

initialize()
