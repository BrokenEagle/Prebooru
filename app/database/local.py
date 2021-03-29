# APP/DATABASE/LOCAL.PY


# ##PYTHON IMPORTS
import time


# ##LOCAL IMPORTS
from . import base
from ..config import workingdirectory, jsonfilepath


# ##GLOBAL VARIABLES


DATABASE_FILE = workingdirectory + jsonfilepath + 'prebooru-local-data.json'

DATABASE_TABLES = ['posts', 'uploads', 'subscriptions']

DATABASE = None
ID_INDEXES = base.InitializeIDIndexes(DATABASE_TABLES)
OTHER_INDEXES = {
    'uploads': {},
    'posts': {
        'md5': {}
    },
    'subscriptions': {
        'artist_id': {}
    }
}
POST_MD5_INDEX = {}
SUBSCRIPTION_ARTIST_ID_INDEX = {}


# ##FUNCTIONS

#   I/O


def LoadDatabase():
    global DATABASE
    DATABASE = base.LoadDatabaseFile("LOCAL", DATABASE_FILE, DATABASE_TABLES, False)
    base.SetIndexes(ID_INDEXES, OTHER_INDEXES, DATABASE)


def SaveDatabase():
    base.SaveDatabaseFile("LOCAL", DATABASE, DATABASE_FILE, False)


#   Create


def CreateUpload(type, uploader_id, request_url=None, subscription_id=None):
    data = {
        'id': GetCurrentIndex('uploads') + 1,
        'uploader_id': uploader_id,
        'subscription_id': subscription_id,
        'request': request_url,
        'type': type,
        'post_ids': [],
        'successes': 0,
        'failures': 0,
        'errors': [],
        'created': round(time.time()),
    }
    base.CommitData(DATABASE, 'uploads', ID_INDEXES, OTHER_INDEXES, data)
    return data


def CreatePost(illust_id, image_id, artist_id, site_id, file_url, md5, size, order):
    data = {
        'id': GetCurrentIndex('posts') + 1,
        'illust_id': illust_id,
        'image_id': image_id,
        'artist_id': artist_id,
        'site_id': site_id,
        'file_url': file_url,
        'md5': md5,
        'size': size,
        'order': order,
        'created': round(time.time()),
        'expires': 0
    }
    base.CommitData(DATABASE, 'posts', ID_INDEXES, OTHER_INDEXES, data)
    return data


def CreateSubscription(artist_id, site_id, user_id):
    data = {
        'id': GetCurrentIndex('subscriptions') + 1,
        'artist_id': artist_id,
        'site_id': site_id,
        'user_id': user_id,
        'errors': None,
        'requery': 0
    }
    base.CommitData(DATABASE, 'subscriptions', ID_INDEXES, OTHER_INDEXES, data)
    return data


#   Misc


def FindByID(table, id):
    return base.FindByID(ID_INDEXES, table, id)


def FindBy(table, key, value):
    return base.FindBy(OTHER_INDEXES, DATABASE, table, key, value)


def GetCurrentIndex(type):
    return base.GetCurrentIndex(DATABASE, type)
