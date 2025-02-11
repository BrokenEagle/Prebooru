# APP/MODELS/ARCHIVE.PY

# ## PACKAGE IMPORTS
from utility.obj import memoized_classproperty
from utility.data import merge_dicts, swap_list_values, dict_prune, swap_key_value

# ## LOCAL IMPORTS
from .model_enums import ArchiveType
from .archive_post import ArchivePost
from .archive_illust import ArchiveIllust
from .archive_artist import ArchiveArtist
from .archive_booru import ArchiveBooru
from .base import JsonModel, integer_column, enum_column, timestamp_column, register_enum_column, relationship


# ## CLASSES

class Archive(JsonModel):
    # #### Columns
    id = integer_column(primary_key=True)
    type_id = enum_column(foreign_key='archive_type.id', nullable=False)
    expires = timestamp_column(nullable=True)

    # ## Relationships
    post_data = relationship(ArchivePost, uselist=False, cascade='all,delete')
    illust_data = relationship(ArchiveIllust, uselist=False, cascade='all,delete')
    artist_data = relationship(ArchiveArtist, uselist=False, cascade='all,delete')
    booru_data = relationship(ArchiveBooru, uselist=False, cascade='all,delete')

    @property
    def subdata(self):
        switcher = {
            'post': lambda: self.post_data,
            'illust': lambda: self.illust_data,
            'artist': lambda: self.artist_data,
            'booru': lambda: self.booru_data,
            'unknown': lambda: None,
        }
        return switcher[self.type_name]()

    @property
    def subdata_json(self):
        if self.subdata is not None:
            return dict_prune(self.subdata.to_json(), 'archive_id')
        return None

    def to_json(self):
        base_json = super().to_json()
        if self.subdata is not None:
            subdata_json = self.subdata_json
            if self.type_name == 'post':
                swap_key_value(subdata_json, 'type', 'post_type')
            return merge_dicts(base_json, subdata_json)
        return base_json

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @memoized_classproperty
    def json_attributes(cls):
        mapping = {
            'type_id': ('archive_type', 'type_name'),
        }
        return swap_list_values(super().json_attributes, mapping)


# ## Initialize

def initialize():
    register_enum_column(Archive, ArchiveType, 'type')
