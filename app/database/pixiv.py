# APP/DATABASE/PIXIV.PY


# ##PYTHON IMPORTS
import urllib


# ##LOCAL IMPORTS
from . import base
from ..logical.utility import ProcessTimestamp
from ..config import workingdirectory, jsonfilepath


# ##GLOBAL VARIABLES


DATABASE_FILE = workingdirectory + jsonfilepath + 'prebooru-pixiv-data.json'

DATABASE_TABLES = ['artists', 'illusts']

DATABASE = None
ID_INDEXES = base.InitializeIDIndexes(DATABASE_TABLES)
OTHER_INDEXES = {
    'artists': {
        'artist_id': {}
    },
    'illusts': {
        'illust_id': {}
    }
}


# ##FUNCTIONS

#   I/O


def LoadDatabase():
    global DATABASE
    DATABASE = base.LoadDatabaseFile("PIXIV", DATABASE_FILE, DATABASE_TABLES, True)
    base.SetIndexes(ID_INDEXES, OTHER_INDEXES, DATABASE)


def SaveDatabase():
    base.SaveDatabaseFile("PIXIV", DATABASE, DATABASE_FILE, True)


#   Create


def CreateIllustFromIllust(pixiv_data, commit=True):
    data = {
        'id': GetCurrentIndex('illusts') + 1,
        'illust_id': int(pixiv_data['illustId']),
        'title': pixiv_data['title'],
        'description': pixiv_data['extraData']['meta']['twitter']['description'],
        'created': ProcessTimestamp(pixiv_data['createDate']),
        'uploaded': ProcessTimestamp(pixiv_data['uploadDate']),
        'images': [
            {
                'url': urllib.parse.urlparse(pixiv_data['urls']['original']).path,
                'width': pixiv_data['width'],
                'height': pixiv_data['height']
            }],
        'tags': [tag['tag'] for tag in pixiv_data['tags']['tags']],
        'artist_id': int(pixiv_data['userId']),
        'pages': pixiv_data['pageCount'],
        'bookmarks': pixiv_data['bookmarkCount'],
        'likes': pixiv_data['likeCount'],
        'replies': pixiv_data['responseCount'],
        'views': pixiv_data['viewCount'],
        'original': pixiv_data['isOriginal'],
        'requery': 0,
        'errors': None
    }
    if commit:
        base.CommitData(DATABASE, 'illusts', ID_INDEXES, OTHER_INDEXES, data)
    return data


def CreateArtistFromIllust(pixiv_data):
    data = {
        'id': GetCurrentIndex('artists') + 1,
        'artist_id': int(pixiv_data['userId']),
        'name': pixiv_data['userName'],
        'account': pixiv_data['userAccount'],
        'profile': "",
        'webpages': [],
        'requery': 0,
        'errors': None
    }
    base.CommitData(DATABASE, 'artists', ID_INDEXES, OTHER_INDEXES, data)
    return data


def CreateArtistFromArtist(pixiv_data):
    print("CreateArtistFromArtist")
    data = {
        'id': int(pixiv_data['userId']),
        'account': None,
        'requery': 0,
        'errors': None
    }
    UpdateArtistFromUser(data, pixiv_data)
    base.CommitData(DATABASE, 'artists', ID_INDEXES, OTHER_INDEXES, data)
    return data


#   Update


def UpdateIllustFromIllust(illust, pixiv_data):
    mapped_data = CreateIllustFromIllust(pixiv_data, False)
    for key in mapped_data:
        illust[key] = mapped_data[key]


def UpdateIllustFromPages(illust, pixiv_data):
    illust['images'] = []
    for image in pixiv_data:
        illust['images'] += [
            {
                'url': urllib.parse.urlparse(image['urls']['original']).path,
                'width': image['width'],
                'height': image['height']
            }
        ]


def UpdateArtistFromUser(artist, pixiv_data):
    artist['name'] = pixiv_data['name']
    artist['profile'] = pixiv_data['comment']
    if pixiv_data['webpage'] is not None:
        artist['webpages'].append(pixiv_data['webpage'])
    for site in pixiv_data['social']:
        artist['webpages'].append(pixiv_data['social'][site]['url'])
    artist['webpages'] = list(set(artist['webpages']))


#   Misc


def FindByID(table, id):
    return base.FindByID(ID_INDEXES, table, id)


def FindBy(table, key, value):
    return base.FindBy(OTHER_INDEXES, DATABASE, table, key, value)


def GetCurrentIndex(type):
    return base.GetCurrentIndex(DATABASE, type)
