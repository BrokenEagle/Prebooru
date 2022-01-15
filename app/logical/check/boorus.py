# APP/LOGICAL/CHECK/BOORUS.PY

# ## LOCAL IMPORTS
from ...models import Booru
from ..database.booru_db import update_booru_from_parameters
from ..sources.danbooru import get_artists_by_ids


# ## FUNCTIONS

def check_all_boorus():
    print("Checking all boorus for updated data.")
    boorus_page = Booru.query.count_paginate(per_page=100)
    if len(boorus_page.items) == 0:
        return
    while True:
        print("\n%d/%d" % (boorus_page.page, boorus_page.pages))
        if not check_boorus(boorus_page.items) or not boorus_page.has_next:
            return
        boorus_page = boorus_page.next()


def check_boorus(boorus):
    danbooru_ids = [booru.danbooru_id for booru in boorus]
    results = get_artists_by_ids(danbooru_ids)
    if results['error']:
        print(results['message'])
        return False
    for data in results['artists']:
        booru = next(filter(lambda x: x.danbooru_id == data['id'], boorus))
        updates = {'current_name': data['name'], 'deleted': data['is_deleted'], 'banned': data['is_banned']}
        update_booru_from_parameters(booru, updates)
    return True
