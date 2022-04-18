# APP/MODELS/POST.PY

# ## PYTHON IMPORTS
import os
import itertools

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS

# ## LOCAL IMPORTS
from .. import DB
from ..logical.utility import unique_objects
from .error import Error
from .illust_url import IllustUrl
from .subscription_pool_element import SubscriptionPoolElement
from .notation import Notation
from .tag import UserTag
from .pool_element import PoolPost, pool_element_delete
from .similarity_data import SimilarityData
from .similarity_pool import SimilarityPool
from .similarity_pool_element import SimilarityPoolElement
from .base import JsonModel, image_server_url


# ## GLOBAL VARIABLES

# Many-to-many tables

PostIllustUrls = DB.Table(
    'post_illust_urls',
    DB.Column('illust_url_id', DB.Integer, DB.ForeignKey('illust_url.id'), primary_key=True),
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
)

PostErrors = DB.Table(
    'post_errors',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)

PostNotations = DB.Table(
    'post_notations',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
)

PostTags = DB.Table(
    'post_tags',
    DB.Column('tag_id', DB.Integer, DB.ForeignKey('tag.id'), primary_key=True),
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
)


# ## CLASSES

class Post(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    file_ext = DB.Column(DB.String(6), nullable=False)
    md5 = DB.Column(DB.String(255), nullable=False)
    size = DB.Column(DB.Integer, nullable=False)
    danbooru_id = DB.Column(DB.Integer, nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    type = DB.Column(DB.String(50), nullable=False)

    # #### Relationships
    illust_urls = DB.relationship(IllustUrl, secondary=PostIllustUrls, lazy=True,
                                  backref=DB.backref('post', uselist=False, lazy=True))
    errors = DB.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('post', uselist=False, lazy=True))
    subscription_pool_element = DB.relationship(SubscriptionPoolElement, lazy=True, uselist=False,
                                                backref=DB.backref('post', lazy=True, uselist=False))
    notations = DB.relationship(Notation, secondary=PostNotations, lazy=True, cascade='all,delete',
                                backref=DB.backref('post', uselist=False, lazy=True))
    _tags = DB.relationship(UserTag, secondary=PostTags, lazy=True, backref=DB.backref('posts', lazy=True))
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    _pools = DB.relationship(PoolPost, lazy=True, backref=DB.backref('item', lazy=True, uselist=False))
    similarity_data = DB.relationship(SimilarityData, lazy=True, cascade='all,delete',
                                      backref=DB.backref('post', lazy=True, uselist=False))
    # Similarity pools and elements must be deleted specially because of sibling relationships
    similarity_pool = DB.relationship(SimilarityPool, lazy=True, uselist=False,
                                      backref=DB.backref('post', lazy=True, uselist=False))
    similarity_elements = DB.relationship(SimilarityPoolElement, lazy=True,
                                          backref=DB.backref('post', lazy=True, uselist=False))
    # uploads <- Upload (MtM)

    # #### Association proxies
    tags = association_proxy('_tags', 'name')
    pools = association_proxy('_pools', 'pool')

    # ## Property methods

    @memoized_property
    def has_sample(self):
        return self.width > SAMPLE_DIMENSIONS[0] or self.height > SAMPLE_DIMENSIONS[1]\
               or self.file_ext not in ['jpg', 'png', 'gif']

    @memoized_property
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1]

    @property
    def file_url(self):
        return image_server_url('data' + self._partial_network_path + self.file_ext)

    @property
    def sample_url(self):
        return image_server_url('sample' + self._partial_network_path + 'jpg') if self.has_sample else self.file_url

    @property
    def preview_url(self):
        return image_server_url('preview' + self._partial_network_path + 'jpg') if self.has_preview else self.file_url

    @property
    def file_path(self):
        return os.path.join(MEDIA_DIRECTORY, 'data', self._partial_file_path + self.file_ext)

    @property
    def sample_path(self):
        return os.path.join(MEDIA_DIRECTORY, 'sample', self._partial_file_path + 'jpg')\
               if self.has_sample else self.file_path

    @property
    def preview_path(self):
        return os.path.join(MEDIA_DIRECTORY, 'preview', self._partial_file_path + 'jpg')\
               if self.has_preview else self.file_path

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
        return self._similar_pool_element_query.get_count() if self.similarity_pool is not None else 0

    @memoized_property
    def similar_posts(self):
        query = self._similar_pool_element_query
        query = query.options(selectinload(SimilarityPoolElement.post),
                              selectinload(SimilarityPoolElement.sibling).selectinload(SimilarityPoolElement.pool))
        query = query.order_by(SimilarityPoolElement.score.desc())
        return query.limit(10).all()

    # ###### Private

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
    def _similar_pool_element_query(self):
        return SimilarityPoolElement.query.filter(SimilarityPoolElement.pool_id == self.similarity_pool.id)

    # ## Methods

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

    basic_attributes = ['id', 'width', 'height', 'size', 'file_ext', 'md5', 'danbooru_id', 'created', 'type']
    relation_attributes = ['illust_urls', 'uploads', 'tags', 'notations', 'errors', 'similarity_data',
                           'similarity_pool', 'similarity_elements', 'subscription_pool_element']
    searchable_attributes = basic_attributes + relation_attributes
    json_attributes = basic_attributes + ['preview_url', 'sample_url', 'file_url', 'illust_urls', 'errors']
