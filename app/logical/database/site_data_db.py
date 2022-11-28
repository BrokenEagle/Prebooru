# APP/LOGICAL/DATABASE/SITE_DATA_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ..enums import SiteDescriptorEnum
from ...models import TwitterData, PixivData
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

TWITTER_COLUMN_ATTRIBUTES = ['retweets', 'replies', 'quotes']
PIXIV_COLUMN_ATTRIBUTES = ['title', 'bookmarks', 'replies', 'views', 'site_updated', 'site_uploaded']

SITE_DATA_TYPE_DICT = {
    'twitter': 'twitter_data',
    'pixiv': 'pixiv_data',
}


# ## FUNCTIONS

def update_site_data_from_parameters(illust, params):
    if illust.site_data is not None:
        expected_type = SITE_DATA_TYPE_DICT[illust.site.name]
        if illust.site_data.type != expected_type:
            print("Deleting site data!")
            SESSION.delete(illust.site_data)
            SESSION.commit()
            illust.site_data = None
    if illust.site == SiteDescriptorEnum.twitter:
        return update_twitter_site_data(illust, params)
    if illust.site == SiteDescriptorEnum.pixiv:
        return update_pixiv_site_data(illust, params)


def update_twitter_site_data(illust, params):
    if illust.site_data is None:
        illust.site_data = TwitterData(illust_id=illust.id)
        SESSION.add(illust.site_data)
        SESSION.commit()
    update_columns = set(params.keys()).intersection(TWITTER_COLUMN_ATTRIBUTES)
    return update_column_attributes(illust.site_data, update_columns, params)


def update_pixiv_site_data(illust, params):
    if illust.site_data is None:
        illust.site_data = PixivData(illust_id=illust.id)
        SESSION.add(illust.site_data)
        SESSION.commit()
    update_columns = set(params.keys()).intersection(PIXIV_COLUMN_ATTRIBUTES)
    return update_column_attributes(illust.site_data, update_columns, params)
