# APP/MODELS/ARCHIVE_ILLUST.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference, is_string, is_boolean

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import SiteDescriptor
from .notation import notations_json
from .base import JsonModel, integer_column, enum_column, text_column, boolean_column, json_column, timestamp_column,\
    register_enum_column, validate_attachment_json, json_list_proxy

# ## GLOBAL_VARIABLES

WEBPAGES_JSON_DATATYPES = {
    'url': is_string,
    'active': is_boolean
}


# ## CLASSES

class ArchiveArtist(JsonModel):
    # #### Columns
    archive_id = integer_column(foreign_key='archive.id', primary_key=True)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    site_artist_id = integer_column(nullable=False)
    site_created = timestamp_column(nullable=True)
    site_account = text_column(nullable=False)
    name = text_column(nullable=True)
    profile = text_column(nullable=True)
    active = boolean_column(nullable=False)
    primary = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)
    webpages = json_column(nullable=True)
    site_accounts = json_column(nullable=True)
    names = json_column(nullable=True)
    profiles = json_column(nullable=True)
    notations = json_column(nullable=True)
    boorus = json_column(nullable=True)

    # ## Instance properties

    @property
    def webpages_json(self):
        if self.webpages is None:
            return []
        return [{'url': webpage[0], 'active': webpage[1]}
                for webpage in self.webpages]

    @webpages_json.setter
    def webpages_json(self, values):
        if values is None:
            self.webpages = None
        else:
            self.webpages = validate_attachment_json(values, WEBPAGES_JSON_DATATYPES)

    site_accounts_json = json_list_proxy('site_accounts', str)
    names_json = json_list_proxy('names', str)
    profiles_json = json_list_proxy('profiles', str)
    notations_json = notations_json
    boorus_json = json_list_proxy('boorus', int)

    # ## Class properties

    @classproperty(cached=False)
    def json_attributes(cls):
        mapping = {
            'site_id': ('site', 'site_name'),
            'webpages': ('webpages', 'webpages_json'),
            'site_accounts': ('site_accounts', 'site_accounts_json'),
            'names': ('names', 'names_json'),
            'profiles': ('profiles', 'profiles_json'),
            'notations': ('notations', 'notations_json'),
            'boorus': ('boorus', 'boorus_json'),
        }
        return [mapping.get(k, k) for k in list_difference(super().json_attributes, ['archive_id'])]

    @classproperty(cached=False)
    def recreate_attributes(cls):
        mapping = {
            'site_id': 'site_name',
        }
        return [mapping.get(k, k) for k in super().recreate_attributes]


# ## Initialize

def initialize():
    DB.Index(None, ArchiveArtist.site_artist_id, ArchiveArtist.site_id, unique=True)
    register_enum_column(ArchiveArtist, SiteDescriptor, 'site')
