# APP/HELPERS/API_DATA_HELPER.PY

# ##LOCAL IMPORTS
from ..logical.sites import get_site_key


# ## FUNCTIONS

def get_site_name(archive_data):
    return get_site_key(archive_data.site_id).title()
