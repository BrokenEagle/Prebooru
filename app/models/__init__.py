# APP/MODELS/__INIT__.PY

# ## LOCAL IMPORTS
from .. import DB


# ## COLLATION IMPORTS

# #### Site data
from .tag import Tag  # noqa: F401
from .label import Label  # noqa: F401
from .description import Description  # noqa: F401
from .site_data import SiteData, PixivData, TwitterData  # noqa: F401
from .illust_url import IllustUrl  # noqa: F401
from .illust import Illust  # noqa: F401
from .artist_url import ArtistUrl  # noqa: F401
from .artist import Artist  # noqa: F401
from .booru import Booru  # noqa: F401

# #### Local data
from .error import Error  # noqa: F401
from .post import Post  # noqa: F401
from .upload_url import UploadUrl  # noqa: F401
from .upload import Upload  # noqa: F401
from .notation import Notation  # noqa: F401
from .pool import Pool  # noqa: F401
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation  # noqa: F401
from .subscription import Subscription  # noqa: F401


# ## INITIALIZATION

IllustUrl.uploads = DB.relationship(Upload, backref=DB.backref('illust_url', lazy=True), lazy=True)
PoolElement.polymorphic_columns = {
    'post_id': PoolPost,
    'illust_id': PoolIllust,
    'notation_id': PoolNotation,
}
PoolElement.polymorphic_relations = {
    'post': PoolPost,
    'illust': PoolIllust,
    'notation': PoolNotation,
}

# ## GLOBAL VARIABLES

NONCE = None
