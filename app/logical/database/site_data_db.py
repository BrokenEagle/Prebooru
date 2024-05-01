# APP/LOGICAL/DATABASE/SITE_DATA_DB.PY

# ## LOCAL IMPORTS
from ...models import TwitterData, PixivData
from .base_db import set_column_attributes, commit_or_flush, add_record, delete_record


# ## GLOBAL VARIABLES

TWITTER_COLUMN_ATTRIBUTES = ['retweets', 'replies', 'quotes']
PIXIV_COLUMN_ATTRIBUTES = ['title', 'bookmarks', 'replies', 'views', 'site_updated', 'site_uploaded']

SITE_DATA_TYPE_DICT = {
    'twitter': 'twitter_data',
    'pixiv': 'pixiv_data',
}


# ## FUNCTIONS

def update_site_data_from_parameters(illust, params, commit=True):
    if illust.site_data is not None:
        expected_type = SITE_DATA_TYPE_DICT[illust.site.name]
        if illust.site_data.type.name != expected_type:
            print("Deleting site data!")
            delete_record(illust.site_data)
            commit_or_flush(True)
            illust.site_data = None
    if illust.site.name == 'twitter':
        result = update_twitter_site_data(illust, params)
    if illust.site.name == 'pixiv':
        result = update_pixiv_site_data(illust, params)
    commit_or_flush(commit)
    return result


def update_twitter_site_data(illust, params):
    if illust.site_data is None:
        illust.site_data = TwitterData(illust_id=illust.id)
        add_record(illust.site_data)
        commit_or_flush(False)
    return set_column_attributes(illust.site_data, TWITTER_COLUMN_ATTRIBUTES, [], params)


def update_pixiv_site_data(illust, params):
    if illust.site_data is None:
        illust.site_data = PixivData(illust_id=illust.id)
        add_record(illust.site_data)
        commit_or_flush(False)
    return set_column_attributes(illust.site_data, PIXIV_COLUMN_ATTRIBUTES, [], params)
