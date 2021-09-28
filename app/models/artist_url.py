# APP/MODELS/ARTIST_URL.PY

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class ArtistUrl(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # ## Class properties

    basic_attributes = ['id', 'artist_id', 'url', 'active']
    relation_attributes = ['artist']
    searchable_attributes = basic_attributes + relation_attributes
    json_attributes = basic_attributes


# ## INITIALIZATION

def initialize():
    ArtistUrl.set_relation_properties()
