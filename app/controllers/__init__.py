# APP/CONTROLLERS/__INIT__.PY

"""Directly interacts with routes."""

# ## PACKAGE_IMPORTS
from config import HAS_EXTERNAL_IMAGE_SERVER

# ## COLLATION IMPORTS
from . import base_controller as base  # noqa: F401

# #### Site data
from . import artists_controller as artist  # noqa: F401
from . import artist_urls_controller as artist_url  # noqa: F401
from . import illusts_controller as illust  # noqa: F401
from . import illust_urls_controller as illust_url  # noqa: F401
from . import boorus_controller as booru  # noqa: F401

# #### Local data
from . import posts_controller as post  # noqa: F401
from . import uploads_controller as upload  # noqa: F401
from . import subscriptions_controller as subscription  # noqa: F401
from . import subscription_elements_controller as subscription_element  # noqa: F401
from . import pools_controller as pool  # noqa: F401
from . import pool_elements_controller as pool_element  # noqa: F401
from . import tags_controller as tag  # noqa: F401
from . import notations_controller as notation  # noqa: F401
from . import errors_controller as error  # noqa: F401

# #### Other DB data
from . import api_data_controller as api_data  # noqa: F401
from . import archives_controller as archive  # noqa: F401
from . import media_files_controller as media_file  # noqa: F401
from . import image_hashes_controller as image_hash  # noqa: F401
from . import similarity_pools_controller as similarity_pool  # noqa: F401
from . import similarity_pool_elements_controller as similarity_pool_element  # noqa: F401

# #### Misc
from . import proxy_controller as proxy  # noqa: F401
from . import static_controller as static  # noqa: F401
from . import tasks_controller as task  # noqa: F401
if not HAS_EXTERNAL_IMAGE_SERVER:
    from . import media_controller as media  # noqa: F401
