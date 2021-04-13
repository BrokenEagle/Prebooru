# APP/MODELS/ARTIST_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class ArtistUrl(JsonModel):
    id: int
    artist_id: int
    url: str
    active: bool
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    basic_attributes = ['id', 'artist_id', 'url', 'active']
    relation_attributes = ['artist']
    searchable_attributes = basic_attributes + relation_attributes
