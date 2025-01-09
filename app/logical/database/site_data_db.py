# APP/LOGICAL/DATABASE/SITE_DATA_DB.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_warning

# ## LOCAL IMPORTS
from ...models import TwitterData, PixivData
from .base_db import set_column_attributes, delete_record, save_record, commit_session


# ## GLOBAL VARIABLES

TWITTER_COLUMN_ATTRIBUTES = ['illust_id', 'retweets', 'replies', 'quotes']
PIXIV_COLUMN_ATTRIBUTES = ['illust_id', 'title', 'bookmarks', 'replies', 'views', 'site_updated', 'site_uploaded']

SITE_DATA_TYPE_DICT = {
    'twitter': 'twitter_data',
    'pixiv': 'pixiv_data',
}

SITE_DATA_MODEL_DICT = {
    'twitter': TwitterData,
    'pixiv': PixivData,
}


# ## FUNCTIONS

# #### Create

def create_site_data_from_parameters(createparams, commit=True):
    site_data = SITE_DATA_MODEL_DICT[createparams['site']]()
    return set_site_data_from_parameters(site_data, createparams, 'created', commit)


# #### Update

def update_site_data_from_parameters(site_data, updateparams, commit=True):
    expected_type = SITE_DATA_TYPE_DICT[updateparams['site']]
    if site_data.model_name != expected_type:
        print_warning("Deleting site data!")
        delete_record(site_data)
        commit_session()
        site_data = SITE_DATA_MODEL_DICT[updateparams['site']]()
    return set_site_data_from_parameters(site_data, updateparams, 'created', commit)


# #### Set

def set_site_data_from_parameters(site_data, setparams, action, commit):
    if site_data.model_name == 'twitter_data':
        col_result = set_column_attributes(site_data, TWITTER_COLUMN_ATTRIBUTES, [], setparams)
    elif site_data.model_name == 'pixiv_data':
        col_result = set_column_attributes(site_data, PIXIV_COLUMN_ATTRIBUTES, [], setparams)
    if col_result:
        save_record(site_data, action, commit=commit)
    return col_result
