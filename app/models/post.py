# APP/MODELS/POST.PY

# ## PYTHON IMPORTS
import os
import itertools

# ## EXTERNAL IMPORTS
from flask import has_app_context
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, ALTERNATE_MEDIA_DIRECTORY, PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from utility.obj import memoized_classproperty
from utility.data import swap_list_values, dict_prune, dict_filter

# ## LOCAL IMPORTS
from ..logical.utility import unique_objects
from .model_enums import PostType
from .error import Error
from .illust_url import IllustUrl
from .subscription_element import SubscriptionElement
from .notation import Notation
from .tag import UserTag, user_tag_creator
from .pool_element import PoolElement
from .image_hash import ImageHash
from .similarity_match import SimilarityMatch
from .base import JsonModel, integer_column, enum_column, text_column, boolean_column, real_column, md5_column,\
    timestamp_column, secondarytable, image_server_url, register_enum_column, relationship, backref


# ## GLOBAL VARIABLES

# Many-to-many tables

PostTags = secondarytable('post_tags', ('post_id', 'post.id'), ('tag_id', 'tag.id'))


# ## FUNCTIONS

def check_app_context(func):
    def wrapper(*args):
        if not has_app_context():
            return None
        return func(*args)
    return wrapper


# ## CLASSES

class Post(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    width = integer_column(nullable=False)
    height = integer_column(nullable=False)
    file_ext = text_column(nullable=False)
    md5 = md5_column(index=True, unique=True, nullable=False)
    size = integer_column(nullable=False)
    danbooru_id = integer_column(nullable=True)
    created = timestamp_column(nullable=False)
    type_id = enum_column(foreign_key='post_type.id', nullable=False)
    alternate = boolean_column(nullable=False)
    pixel_md5 = md5_column(nullable=True)
    duration = real_column(nullable=True)
    audio = boolean_column(nullable=True)
    simcheck = boolean_column(nullable=False)

    # ## Relationships
    illust_urls = relationship(IllustUrl, uselist=True, backref=backref('post', uselist=False))
    errors = relationship(Error, uselist=True, cascade='all,delete', backref=backref('post', uselist=False))
    subscription_element = relationship(SubscriptionElement, uselist=False, backref=backref('post', uselist=False))
    notations = relationship(Notation, uselist=True, cascade='all,delete', backref=backref('post', uselist=False))
    tags = relationship(UserTag, secondary=PostTags, uselist=True)
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    pool_elements = relationship(PoolElement, uselist=True, backref=backref('post', uselist=False))
    image_hashes = relationship(ImageHash, cascade='all,delete', backref=backref('post', uselist=False))
    similarity_matches_forward = relationship(SimilarityMatch, cascade='all,delete',
                                              backref=backref('forward_post', uselist=False),
                                              foreign_keys=[SimilarityMatch.forward_id])
    similarity_matches_reverse = relationship(SimilarityMatch, cascade='all,delete',
                                              backref=backref('reverse_post', uselist=False),
                                              foreign_keys=[SimilarityMatch.reverse_id])

    # ## Association proxies
    tag_names = association_proxy('tags', 'name', creator=user_tag_creator)
    pools = association_proxy('pool_elements', 'pool')

    # ## Instance properties

    @property
    def is_video(self):
        return self.file_ext in ['mp4']

    @property
    def has_sample(self):
        return self.width > SAMPLE_DIMENSIONS[0] or self.height > SAMPLE_DIMENSIONS[1] or self.is_video

    @property
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1] or self.is_video

    @property
    def video_sample_exists(self):
        return os.path.exists(self.video_sample_path)

    @property
    def is_alternate(self):
        return self.alternate and ALTERNATE_MEDIA_DIRECTORY is not None

    @property
    def suburl_path(self):
        return 'main' if not self.is_alternate else 'alternate'

    @property
    @check_app_context
    def file_url(self):
        return image_server_url('data' + self._partial_network_path + self.file_ext, subtype=self.suburl_path)

    @property
    @check_app_context
    def sample_url(self):
        return image_server_url('sample' + self._partial_network_path + 'jpg', subtype=self.suburl_path)\
            if self.has_sample else self.file_url

    @property
    @check_app_context
    def preview_url(self):
        return image_server_url('preview' + self._partial_network_path + 'jpg', subtype=self.suburl_path)\
            if self.has_preview else self.file_url

    @property
    @check_app_context
    def video_sample_url(self):
        return image_server_url('video_sample' + self._partial_network_path + 'webm', subtype=self.suburl_path)\
            if self.is_video else None

    @property
    @check_app_context
    def video_preview_url(self):
        return image_server_url('video_preview' + self._partial_network_path + 'webp', subtype=self.suburl_path)\
            if self.is_video else None

    @property
    def subdirectory_path(self):
        return MEDIA_DIRECTORY if not self.is_alternate else ALTERNATE_MEDIA_DIRECTORY

    @property
    def file_path(self):
        return os.path.join(self.subdirectory_path, 'data', self._partial_file_path + self.file_ext)

    @property
    def sample_path(self):
        return os.path.join(self.subdirectory_path, 'sample', self._partial_file_path + 'jpg')\
            if self.has_sample else None

    @property
    def preview_path(self):
        return os.path.join(self.subdirectory_path, 'preview', self._partial_file_path + 'jpg')\
            if self.has_preview else None

    @property
    def video_sample_path(self):
        return os.path.join(self.subdirectory_path, 'video_sample', self._partial_file_path + 'webm')\
            if self.is_video else None

    @property
    def video_preview_path(self):
        return os.path.join(self.subdirectory_path, 'video_preview', self._partial_file_path + 'webp')\
            if self.is_video else None

    @property
    def similarity_matches(self):
        return self.similarity_matches_forward + self.similarity_matches_reverse

    @memoized_property
    def related_posts(self):
        from .illust import Illust
        query = Post.query.join(IllustUrl, Post.illust_urls)
        query = query.filter(IllustUrl.illust_id.in_(self._illust_query.with_entities(Illust.id)))
        query = query.group_by(Post.id)
        query = query.order_by(IllustUrl.illust_id.asc(), IllustUrl.order.asc())
        return query.limit(10).all()

    @memoized_property
    def selectin_illusts(self):
        return unique_objects([illust_url.illust for illust_url in self.illust_urls])

    @memoized_property
    def selectin_artists(self):
        return unique_objects([illust.artist for illust in self.selectin_illusts])

    @memoized_property
    def selectin_boorus(self):
        return unique_objects(list(itertools.chain(*[artist.boorus for artist in self.selectin_artists])))

    @memoized_property
    def illusts(self):
        return self._illust_query.all()

    @memoized_property
    def artists(self):
        return self._artist_query.all()

    @memoized_property
    def boorus(self):
        return self._booru_query.all()

    @memoized_property
    def similar_post_count(self):
        return self._similar_match_query.get_count()

    @memoized_property
    def similar_posts(self):
        query = self._similar_match_query
        query = query.options(selectinload(SimilarityMatch.forward_post),
                              selectinload(SimilarityMatch.reverse_post))
        query = query.order_by(SimilarityMatch.score.desc(),
                               SimilarityMatch.forward_id.desc(),
                               SimilarityMatch.reverse_id.desc())
        return query.limit(10).all()

    @property
    def illust_urls_json(self):
        return [dict_prune(illust_url.to_json(), ['id', 'post_id']) for illust_url in self.illust_urls]

    @property
    def errors_json(self):
        return [dict_filter(error.to_json(), ['module', 'message', 'created']) for error in self.errors]

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @memoized_classproperty
    def json_attributes(cls):
        return cls.repr_attributes + ['preview_url', 'sample_url', 'file_url', ('tags', 'tag_names'),
                                      ('illust_urls', 'illust_urls_json'), ('errors', 'errors_json')]

    # ## Private

    @memoized_property
    def _partial_network_path(self):
        return '/%s/%s/%s.' % (self.md5[0:2], self.md5[2:4], self.md5)

    @memoized_property
    def _partial_file_path(self):
        return os.path.join(self.md5[0:2], self.md5[2:4], self._file_name)

    @memoized_property
    def _file_name(self):
        return '%s.' % (self.md5)

    @property
    def _similar_match_query(self):
        clause = or_(SimilarityMatch.forward_id == self.id, SimilarityMatch.reverse_id == self.id)
        return SimilarityMatch.query.filter(clause)

    @property
    def _illust_query(self):
        from .illust import Illust
        return Illust.query.join(IllustUrl, Illust.urls).filter(IllustUrl.post_id == self.id).group_by(Illust.id)

    @property
    def _artist_query(self):
        from .illust import Illust
        from .artist import Artist
        return Artist.query.join(Illust, Artist.illusts).join(IllustUrl, Illust.urls)\
                           .filter(IllustUrl.post_id == self.id).group_by(Artist.id)

    @property
    def _booru_query(self):
        from .illust import Illust
        from .artist import Artist
        from .booru import Booru
        return Booru.query.join(Artist, Booru.artists).join(Illust, Artist.illusts).join(IllustUrl, Illust.urls)\
                          .filter(IllustUrl.post_id == self.id).group_by(Booru.id)


# ## INITIALIZATION

def initialize():
    register_enum_column(Post, PostType, 'type')
