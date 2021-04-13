# APP/CONTROLLERS/__INIT__.PY

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
from . import pools_controller as pool  # noqa: F401
from . import pool_elements_controller as pool_element  # noqa: F401
from . import tags_controller as tag  # noqa: F401
from . import notations_controller as notation  # noqa: F401
from . import errors_controller as error  # noqa: F401

# #### Other DB data
from . import similarity_controller as similarity  # noqa: F401
from . import similarity_pools_controller as similarity_pool  # noqa: F401
from . import similarity_pool_elements_controller as similarity_pool_element  # noqa: F401

# #### Misc
from . import proxy_controller as proxy  # noqa: F401
from . import static_controller as static  # noqa: F401
