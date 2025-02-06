# APP/MODELS/ARCHIVE.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import merge_dicts

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import ArchiveType
from .archive_post import ArchivePost
from .archive_illust import ArchiveIllust
from .archive_artist import ArchiveArtist
from .base import JsonModel, integer_column, enum_column, text_column, json_column, timestamp_column,\
    register_enum_column, relationship


# ## CLASSES

class Archive(JsonModel):
    # #### Columns
    id = integer_column(primary_key=True)
    type_id = enum_column(foreign_key='archive_type.id', nullable=False)
    key = text_column(nullable=False)
    data = json_column(nullable=False)
    expires = timestamp_column(nullable=True)

    # ## Relationships
    post_data = relationship(ArchivePost, uselist=False, cascade='all,delete')
    illust_data = relationship(ArchiveIllust, uselist=False, cascade='all,delete')
    artist_data = relationship(ArchiveArtist, uselist=False, cascade='all,delete')

    @property
    def subdata(self):
        switcher = {
            'post': lambda: self.post_data,
            'illust': lambda: self.illust_data,
            'artist': lambda: self.artist_data,
            'unknown': lambda: None,
        }
        return switcher[self.type_name]()

    def to_json(self):
        if self.type_name in ['post', 'illust', 'artist']:
            return merge_dicts(super().to_json(), self.subdata.to_json())
        return super().to_json()

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]

    @classproperty(cached=False)
    def json_attributes(cls):
        mapping = {
            'type_id': ('archive_type', 'type_name'),
        }
        return [mapping.get(k, k) for k in super().json_attributes]

    __table_args__ = (
        DB.UniqueConstraint('key', 'type_id'),
    )


# ## Initialize

def initialize():
    register_enum_column(Archive, ArchiveType, 'type')
