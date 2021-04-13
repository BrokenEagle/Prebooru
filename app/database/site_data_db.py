# APP/DATABASE/SITE_DATA_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..sites import Site, GetSiteKey
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES


TWITTER_COLUMN_ATTRIBUTES = ['retweets', 'replies', 'quotes']
PIXIV_COLUMN_ATTRIBUTES = ['title', 'bookmarks', 'replies', 'views', 'site_updated', 'site_uploaded']

SITE_DATA_TYPE_DICT = {
    'TWITTER': 'twitter_data',
    'PIXIV': 'pixiv_data',
}


# ##FUNCTIONS

def UpdateSiteDataFromParameters(site_data, illust_id, site_id, params):
    if site_data is not None:
        site_key = GetSiteKey(site_id)
        expected_type = SITE_DATA_TYPE_DICT[site_key]
        if site_data.type != expected_type:
            print("Deleting site data!")
            SESSION.delete(site_data)
            SESSION.commit()
            site_data = None
    if site_id == Site.TWITTER.value:
        return UpdateTwitterSiteData(site_data, illust_id, params)
    if site_id == Site.PIXIV.value:
        return UpdatePixivSiteData(site_data, illust_id, params)


def UpdateTwitterSiteData(site_data, illust_id, params):
    if site_data is None:
        site_data = models.TwitterData(illust_id=illust_id)
        SESSION.add(site_data)
        SESSION.commit()
    update_columns = set(params.keys()).intersection(TWITTER_COLUMN_ATTRIBUTES)
    return UpdateColumnAttributes(site_data, update_columns, params)


def UpdatePixivSiteData(site_data, illust_id, params):
    if site_data is None:
        site_data = models.PixivData(illust_id=illust_id)
        SESSION.add(site_data)
        SESSION.commit()
    update_columns = set(params.keys()).intersection(PIXIV_COLUMN_ATTRIBUTES)
    return UpdateColumnAttributes(site_data, update_columns, params)
