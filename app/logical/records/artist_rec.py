# APP/LOGICAL/RECORDS/ARTIST_REC.PY

# ## LOCAL IMPORTS
from ..database.artist_db import create_artist_from_parameters, update_artist_from_parameters


# ## FUNCTIONS

def create_artist_from_source(site_artist_id, source):
    params = source.get_artist_data(site_artist_id)
    if not params['active']:
        return
    return create_artist_from_parameters(params)


def update_artist_from_source(artist, source):
    params = source.get_artist_data(artist.site_artist_id)
    if params['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        params['webpages'] += ['-' + w.url for w in artist.webpages if w.url not in params['webpages']]
        params['names'] += [an.name for an in artist.names if an.name not in params['names']]
        params['site_accounts'] += [sa.name for sa in artist.site_accounts if sa.name not in params['site_accounts']]
    update_artist_from_parameters(artist, params)
