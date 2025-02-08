# APP/MODELS/ARCHIVE_ILLUST.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference, is_integer, is_string, is_string_or_none, is_boolean

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import SiteDescriptor
from .notation import notations_json
from .base import JsonModel, integer_column, enum_column, text_column, boolean_column, json_column, timestamp_column,\
    register_enum_column, validate_attachment_json, json_list_proxy

# ## GLOBAL_VARIABLES

URLS_JSON_DATATYPES = {
    'order': is_integer,
    'url': is_string,
    'sample': is_string_or_none,
    'height': is_integer,
    'width': is_integer,
    'active': is_boolean,
    'md5': is_string_or_none
}


# ## CLASSES

class ArchiveIllust(JsonModel):
    # #### Columns
    archive_id = integer_column(foreign_key='archive.id', primary_key=True)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    site_illust_id = integer_column(nullable=False)
    site_artist_id = integer_column(nullable=False)
    site_created = timestamp_column(nullable=True)
    title = text_column(nullable=True)
    commentary = text_column(nullable=True)
    pages = integer_column(nullable=False)
    score = integer_column(nullable=False)
    active = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)
    urls = json_column(nullable=True)
    titles = json_column(nullable=True)
    commentaries = json_column(nullable=True)
    additional_commentaries = json_column(nullable=True)
    tags = json_column(nullable=True)
    notations = json_column(nullable=True)

    # ## Instance properties

    @property
    def urls_json(self):
        if self.urls is None:
            return []
        return [{'order': url[0], 'url': url[1], 'sample': url[2], 'height': url[3],
                 'width': url[4], 'active': url[5], 'md5': url[6]}
                for url in self.urls]

    @urls_json.setter
    def urls_json(self, values):
        if values is None:
            self.urls = None
        else:
            self.urls = validate_attachment_json(values, URLS_JSON_DATATYPES)

    titles_json = json_list_proxy('titles', str)
    commentaries_json = json_list_proxy('commentaries', str)
    additional_commentaries_json = json_list_proxy('additional_commentaries', str)
    tags_json = json_list_proxy('tags', str)
    notations_json = notations_json

    # ## Class properties

    @classproperty(cached=False)
    def json_attributes(cls):
        mapping = {
            'site_id': ('site', 'site_name'),
            'urls': ('urls', 'urls_json'),
            'titles': ('titles', 'titles_json'),
            'commentaries': ('commentaries', 'commentaries_json'),
            'additional_commentaries': ('additional_commentaries', 'additional_commentaries_json'),
            'tags': ('tags', 'tags_json'),
            'notations': ('notations', 'notations_json'),
        }
        return [mapping.get(k, k) for k in list_difference(super().json_attributes, ['archive_id'])]

    @classproperty(cached=False)
    def recreate_attributes(cls):
        return list_difference(super().basic_attributes, ['archive_id', 'urls', 'titles', 'commentaries',
                                                          'additional_commentaries', 'notations', 'tags'])


# ## Initialize

def initialize():
    DB.Index(None, ArchiveIllust.site_illust_id, ArchiveIllust.site_id, unique=True)
    register_enum_column(ArchiveIllust, SiteDescriptor, 'site')
