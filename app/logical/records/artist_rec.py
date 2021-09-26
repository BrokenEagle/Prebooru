# APP/LOGICAL/RECORDS/ARTIST_REC.PY

# ## LOCAL IMPORTS
from ...database.artist_db import create_artist_from_parameters, update_artist_from_parameters


# ## FUNCTIONS

def create_artist_from_source(site_artist_id, source):
    createparams = source.get_artist_data(site_artist_id)
    if not createparams['active']:
        return
    return create_artist_from_parameters(createparams)


def update_artist_from_source(artist, source):
    updateparams = source.get_artist_data(artist.site_artist_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['webpages'] += ['-' + webpage.url for webpage in artist.webpages if webpage.url not in updateparams['webpages']]
        updateparams['names'] += [artist_name.name for artist_name in artist.names if artist_name.name not in updateparams['names']]
        updateparams['site_accounts'] += [site_account.name for site_account in artist.site_accounts if site_account.name not in updateparams['site_accounts']]
    update_artist_from_parameters(artist, updateparams)
