# APP/MODELS/__INIT__.PY

# ## PYTHON IMPORTS
from types import ModuleType

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

# #### Similarity data
from .similarity_data import SimilarityData
from .similarity_pool import SimilarityPool
from .similarity_pool_element import SimilarityPoolElement

# #### Cache data
from .api_data import ApiData
from .media_file import MediaFile
from .domain import Domain


# ## INITIALIZATION

def initialize():
    modules = [m for (k, m) in globals().items() if type(m) is ModuleType and k != '__builtins__' and hasattr(m, 'initialize')]
    for mod in modules:
        mod.initialize()

initialize()

# ## GLOBAL VARIABLES

NONCE = None
