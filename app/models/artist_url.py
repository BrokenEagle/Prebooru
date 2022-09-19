# APP/MODELS/ARTIST_URL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class ArtistUrl(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False, index=True)
    url = DB.Column(DB.String(255), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.webpages.property._configure_started
    ArtistUrl.set_relation_properties()
