# APP/LOGICAL/CHECK/BOORU_ARTISTS.PY

# ## PYTHON IMPORTS
import itertools
from sqlalchemy import not_

# ## LOCAL IMPORTS
from ...models import Artist, Booru
from ...database.booru_db import create_booru_from_parameters, booru_append_artist
from ...sources.danbooru_source import get_artists_by_multiple_urls


# ## GLOBAL VARIABLES

BOORU_PRIMARYJOIN = Artist.boorus.property.primaryjoin
BOORU_SUBQUERY = Artist.query\
    .join(BOORU_PRIMARYJOIN.right.table, BOORU_PRIMARYJOIN.left == BOORU_PRIMARYJOIN.right)\
    .filter(BOORU_PRIMARYJOIN.left == BOORU_PRIMARYJOIN.right).with_entities(Artist.id)
BOORU_SUBCLAUSE = Artist.id.in_(BOORU_SUBQUERY)


# ## FUNCTIONS

def check_all_artists_for_boorus():
    print("Checking all artists for Danbooru artists.")
    query = Artist.query.filter(not_(BOORU_SUBCLAUSE))
    max_id = 0
    page = 1
    page_count = (query.get_count() // 100) + 1
    while True:
        artists = query.filter(Artist.id > max_id).limit(100).all()
        if len(artists) == 0:
            return
        print("\n%d/%d" % (page, page_count))
        if not check_artists_for_boorus(artists):
            return
        max_id = max(artist.id for artist in artists)
        page += 1


def check_artists_for_boorus(artists):
    query_urls = [artist.booru_search_url for artist in artists]
    results = get_artists_by_multiple_urls(query_urls)
    if results['error']:
        print(results['message'])
        return False
    if len(results['data']) > 0:
        booru_artist_ids = set(artist['id'] for artist in itertools.chain(*[results['data'][url] for url in results['data']]))
        boorus = Booru.query.filter(Booru.danbooru_id.in_(booru_artist_ids)).all()
        for url in results['data']:
            add_danbooru_artists(url, results['data'][url], boorus, artists)
    return True


def add_danbooru_artists(url, danbooru_artists, db_boorus, db_artists):
    artist = next(filter(lambda x: x.booru_search_url == url, db_artists))
    for danbooru_artist in danbooru_artists:
        booru = next(filter(lambda x: x.danbooru_id == danbooru_artist['id'], db_boorus), None)
        if booru is None:
            booru = create_booru_from_parameters({'danbooru_id': danbooru_artist['id'], 'current_name': danbooru_artist['name']})
        booru_append_artist(booru, artist)
