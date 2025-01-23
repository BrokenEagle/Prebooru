# APP/MODELS/ARTIST_URL.PY

# ## LOCAL IMPORTS
from .base import JsonModel, integer_column, text_column, boolean_column


# ## CLASSES

class ArtistUrl(JsonModel):
    # #### Columns
    id = integer_column(primary_key=True)
    artist_id = integer_column(foreign_key='artist.id', nullable=False, index=True)
    url = text_column(nullable=False)
    active = boolean_column(nullable=False)

    # ## Relations
    # (MtO) artist [artist]


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.webpages.property._configure_started
    ArtistUrl.set_relation_properties()
