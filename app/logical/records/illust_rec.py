# APP/LOGICAL/RECORDS/ILLUST_REC.PY

# ## LOCAL IMPORTS
from .artist_rec import create_artist_from_source
from ..database.artist_db import get_site_artist
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters


# ## FUNCTIONS

def create_illust_from_source(site_illust_id, source):
    createparams = source.get_illust_data(site_illust_id)
    if not createparams['active']:
        return
    artist = get_site_artist(createparams['site_artist_id'], source.SITE_ID)
    if artist is None:
        artist = create_artist_from_source(createparams['site_artist_id'], source)
        if artist is None:
            return
    createparams['artist_id'] = artist.id
    return create_illust_from_parameters(createparams)


def update_illust_from_source(illust, source):
    updateparams = source.get_illust_data(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag for tag in illust.tags if tag not in updateparams['tags']]
    update_illust_from_parameters(illust, updateparams)
