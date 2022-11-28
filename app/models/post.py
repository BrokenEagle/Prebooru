# APP/MODELS/POST.PY

# ## PYTHON IMPORTS
import os
import itertools

# ## EXTERNAL IMPORTS
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, ALTERNATE_MEDIA_DIRECTORY, PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import PostTypeEnum
from ..logical.utility import unique_objects
from .error import Error
from .illust_url import IllustUrl
from .subscription_element import SubscriptionElement
from .notation import Notation
from .tag import UserTag
from .pool_element import PoolPost, pool_element_delete
from .image_hash import ImageHash
from .similarity_match import SimilarityMatch
from .base import JsonModel, EpochTimestamp, IntEnum, secondarytable, image_server_url, BlobMD5


# ## GLOBAL VARIABLES

# Many-to-many tables

PostIllustUrls = secondarytable(
    'post_illust_urls',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('illust_url_id', DB.Integer, DB.ForeignKey('illust_url.id'), primary_key=True),
    DB.Index(None, 'illust_url_id', 'post_id'),
)

PostErrors = secondarytable(
    'post_errors',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
    DB.Index(None, 'error_id', 'post_id'),
)

PostNotations = secondarytable(
    'post_notations',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
    DB.Index(None, 'notation_id', 'post_id'),
)

PostTags = secondarytable(
    'post_tags',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('tag_id', DB.Integer, DB.ForeignKey('tag.id'), primary_key=True),
)


# ## CLASSES

class Post(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    file_ext = DB.Column(DB.String(6), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=False), index=True, unique=True, nullable=False)
    size = DB.Column(DB.Integer, nullable=False)
    danbooru_id = DB.Column(DB.Integer, nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    type = DB.Column(IntEnum(PostTypeEnum), nullable=False)
    alternate = DB.Column(DB.Boolean, nullable=False)
    pixel_md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    duration = DB.Column(DB.Float, nullable=True)
    audio = DB.Column(DB.Boolean, nullable=True)

    # ## Relationships
    illust_urls = DB.relationship(IllustUrl, secondary=PostIllustUrls, lazy=True,
                                  backref=DB.backref('post', uselist=False, lazy=True))
    errors = DB.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('post', uselist=False, lazy=True))
    subscription_element = DB.relationship(SubscriptionElement, lazy=True, uselist=False,
                                           backref=DB.backref('post', lazy=True, uselist=False))
    notations = DB.relationship(Notation, secondary=PostNotations, lazy=True, cascade='all,delete',
                                backref=DB.backref('post', uselist=False, lazy=True))
    _tags = DB.relationship(UserTag, secondary=PostTags, lazy=True, backref=DB.backref('posts', lazy=True))
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    _pools = DB.relationship(PoolPost, lazy=True, backref=DB.backref('item', lazy=True, uselist=False))
    image_hashes = DB.relationship(ImageHash, lazy=True, cascade='all,delete',
                                   backref=DB.backref('post', lazy=True, uselist=False))
    # Similarity pools and elements must be deleted specially because of sibling relationships
    similarity_matches_forward = DB.relationship(SimilarityMatch, lazy=True, cascade='all,delete',
                                                 backref=DB.backref('forward_post', lazy=True, uselist=False),
                                                 foreign_keys=[SimilarityMatch.forward_id])
    similarity_matches_reverse = DB.relationship(SimilarityMatch, lazy=True, cascade='all,delete',
                                                 backref=DB.backref('reverse_post', lazy=True, uselist=False),
                                                 foreign_keys=[SimilarityMatch.reverse_id])

    # ## Association proxies
    tags = association_proxy('_tags', 'name')
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
        return image_server_url('data' + self._partial_network_path + self.file_ext, subtype=self.suburl_path)

    @property
    def sample_url(self):
        if self.has_sample:
            return image_server_url('sample' + self._partial_network_path + 'jpg', subtype=self.suburl_path)
        return self.file_url

    @property
    def preview_url(self):
        if self.has_preview:
            return image_server_url('preview' + self._partial_network_path + 'jpg', subtype=self.suburl_path)
        return self.file_url

    @property
    def video_sample_url(self):
        if self.is_video:
            return image_server_url('video_sample' + self._partial_network_path + 'webm', subtype=self.suburl_path)

    @property
    def video_preview_url(self):
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
        illust_posts = [illust.posts for illust in self.illusts]
        post_generator = (post for post in itertools.chain(*illust_posts) if post is not None)
        return [post for post in unique_objects(post_generator) if post.id != self.id]

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

    def delete_pool(self, pool_id):
        pool_element_delete(pool_id, self)

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    # ## Class properties

    type_enum = PostTypeEnum

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['preview_url', 'sample_url', 'file_url', 'illust_urls', 'errors']

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
