# APP/HELPERS/API_DATA_HELPER.PY

# ## LOCAL IMPORTS
from ..logical.sites import get_site_key


# ## FUNCTIONS

def get_site_name(api_data):
    return get_site_key(api_data.site_id).title()
