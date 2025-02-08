# APP/MODELS/ARCHIVE_ILLUST.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference, is_string, is_integer

# ## LOCAL IMPORTS
from .. import DB
from .notation import notations_json
from .base import JsonModel, integer_column, text_column, boolean_column, json_column, timestamp_column,\
    validate_attachment_json, json_list_proxy

# ## GLOBAL_VARIABLES

ARTISTS_JSON_DATATYPES = {
    'site': is_string,
    'site_artist_id': is_integer
}


# ## CLASSES

class ArchiveBooru(JsonModel):
    # #### Columns
    archive_id = integer_column(foreign_key='archive.id', primary_key=True)
    danbooru_id = integer_column(nullable=True)
    name = text_column(nullable=False)
    banned = boolean_column(nullable=False)
    deleted = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)
    names = json_column(nullable=True)
    notations = json_column(nullable=True)
    artists = json_column(nullable=True)

    # ## Instance properties

    @property
    def artists_json(self):
        if self.artists is None:
            return []
        return [{'site': artist[0], 'site_artist_id': artist[1]}
                for artist in self.artists]

    @artists_json.setter
    def artists_json(self, values):
        if values is None:
            self.artists = None
        else:
            self.artists = validate_attachment_json(values, ARTISTS_JSON_DATATYPES)

    names_json = json_list_proxy('names', str)
    notations_json = notations_json

    # ## Class properties

    @classproperty(cached=False)
    def json_attributes(cls):
        mapping = {
            'names': ('names', 'names_json'),
            'notations': ('notations', 'notations_json'),
            'artists': ('artists', 'artists_json'),
        }
        return [mapping.get(k, k) for k in list_difference(super().json_attributes, ['archive_id'])]

    @classproperty(cached=False)
    def recreate_attributes(cls):
        return list_difference(super().basic_attributes, ['archive_id', 'names', 'notations', 'artists'])


# ## Initialize

def initialize():
    DB.Index(None, ArchiveBooru.name, unique=True)
