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
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.utility import unique_objects
from .model_enums import PostType
from .error import Error
from .illust_url import IllustUrl
from .subscription_element import SubscriptionElement
from .notation import Notation
from .tag import UserTag, user_tag_creator
from .pool_element import PoolPost, pool_element_delete
from .image_hash import ImageHash
from .similarity_match import SimilarityMatch
from .base import JsonModel, integer_column, enum_column, text_column, boolean_column, real_column, md5_column,\
    timestamp_column, secondarytable, image_server_url, register_enum_column, relationship, backref


# ## GLOBAL VARIABLES

# Many-to-many tables

PostTags = secondarytable('post_tags', ('post_id', 'post.id'), ('tag_id', 'tag.id'))


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
    _pools = relationship(PoolPost, backref=backref('item', uselist=False))
    image_hashes = relationship(ImageHash, cascade='all,delete', backref=backref('post', uselist=False))
    similarity_matches_forward = relationship(SimilarityMatch, cascade='all,delete',
                                              backref=backref('forward_post', uselist=False),
                                              foreign_keys=[SimilarityMatch.forward_id])
    similarity_matches_reverse = relationship(SimilarityMatch, cascade='all,delete',
                                              backref=backref('reverse_post', uselist=False),
                                              foreign_keys=[SimilarityMatch.reverse_id])

    # ## Association proxies
    tag_names = association_proxy('tags', 'name', creator=user_tag_creator)
    pools = association_proxy('_pools', 'pool')

    # ## Instance properties

    @property
    def is_video(self):
        return self.file_ext not in ['jpg', 'png', 'gif']

    @memoized_property
    def has_sample(self):
        return self.width > SAMPLE_DIMENSIONS[0] or self.height > SAMPLE_DIMENSIONS[1] or self.is_video

    @memoized_property
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1] or self.is_video

    @memoized_property
    def video_sample_exists(self):
        return os.path.exists(self.video_sample_path)

    @property
    def is_alternate(self):
        return self.alternate and ALTERNATE_MEDIA_DIRECTORY is not None

    @property
    def suburl_path(self):
        return 'main' if not self.is_alternate else 'alternate'

    @property
    def file_url(self):
        if not has_app_context():
            return None
        return image_server_url('data' + self._partial_network_path + self.file_ext, subtype=self.suburl_path)

    @property
    def sample_url(self):
        if not has_app_context():
            return None
        if self.has_sample:
            return image_server_url('sample' + self._partial_network_path + 'jpg', subtype=self.suburl_path)
        return self.file_url

    @property
    def preview_url(self):
        if not has_app_context():
            return None
        if self.has_preview:
            return image_server_url('preview' + self._partial_network_path + 'jpg', subtype=self.suburl_path)
        return self.file_url

    @property
    def video_sample_url(self):
        if not has_app_context():
            return None
        if self.is_video:
            return image_server_url('video_sample' + self._partial_network_path + 'webm', subtype=self.suburl_path)

    @property
    def video_preview_url(self):
        if not has_app_context():
            return None
        if self.is_video:
            return image_server_url('video_preview' + self._partial_network_path + 'webp', subtype=self.suburl_path)

    @property
    def subdirectory_path(self):
        return MEDIA_DIRECTORY if not self.is_alternate else ALTERNATE_MEDIA_DIRECTORY

    @property
    def file_path(self):
        return os.path.join(self.subdirectory_path, 'data', self._partial_file_path + self.file_ext)

    @property
    def sample_path(self):
        if self.has_sample:
            return os.path.join(self.subdirectory_path, 'sample', self._partial_file_path + 'jpg')

    @property
    def preview_path(self):
        if self.has_preview:
            return os.path.join(self.subdirectory_path, 'preview', self._partial_file_path + 'jpg')

    @property
    def video_sample_path(self):
        if self.is_video:
            return os.path.join(self.subdirectory_path, 'video_sample', self._partial_file_path + 'webm')

    @property
    def video_preview_path(self):
        if self.is_video:
            return os.path.join(self.subdirectory_path, 'video_preview', self._partial_file_path + 'webp')

    @property
    def similarity_matches(self):
        return self.similarity_matches_forward + self.similarity_matches_reverse

    @memoized_property
    def related_posts(self):
        query = Post.query.join(IllustUrl, Post.illust_urls)
        query = query.filter(IllustUrl.illust_id.in_(self.illust_ids), Post.id != self.id)
        query = query.distinct(Post.id)
        query = query.order_by(IllustUrl.illust_id.asc(), IllustUrl.order.asc())
        return query.limit(10).all()

    @memoized_property
    def illusts(self):
        return unique_objects([illust_url.illust for illust_url in self.illust_urls])

    @memoized_property
    def artists(self):
        return unique_objects([illust.artist for illust in self.illusts])

    @memoized_property
    def boorus(self):
        return unique_objects(list(itertools.chain(*[artist.boorus for artist in self.artists])))

    @property
    def illust_ids(self):
        return list(set(illust_url.illust_id for illust_url in self.illust_urls))

    @property
    def artist_ids(self):
        return list(set(illust.artist_id for illust in self.illusts))

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
    def key(self):
        return self.md5

    def delete_pool(self, pool_id):
        pool_element_delete(pool_id, self)

    def attach_illust_url_by_full_url(self, full_url):
        illust_url = IllustUrl.find_by_key(full_url)
        if illust_url is not None:
            illust_url.post = self
            return True
        return False

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    # ## Class properties

    @classmethod
    def find_by_key(cls, key):
        return cls.query.filter(cls.md5 == key)\
                        .one_or_none()

    @classproperty(cached=True)
    def load_columns(cls):
        return super().load_columns + ['type_name']

    archive_excludes = {'type', 'type_id', 'simcheck', 'alternate'}
    archive_includes = {('type', 'type_name')}
    archive_attachments = ['notations', 'errors']
    archive_links = [('illusts', 'illust_urls', 'full_url', 'attach_illust_url_by_full_url')]

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['preview_url', 'sample_url', 'file_url', 'tags', 'illust_urls', 'errors']

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


# ## INITIALIZATION

def initialize():
    register_enum_column(Post, PostType, 'type')
