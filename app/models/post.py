# APP/MODELS/POST.PY

# ##PYTHON IMPORTS
import os
import itertools
import datetime
from types import SimpleNamespace
from typing import List
from dataclasses import dataclass
from sqlalchemy.orm import selectinload
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..config import IMAGE_DIRECTORY, PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from ..logical.utility import UniqueObjects
from ..base_model import JsonModel, RemoveKeys, image_server_url
from .error import Error
from .illust_url import IllustUrl
from .notation import Notation
from .pool_element import PoolPost, pool_element_delete
from .similarity_pool import SimilarityPool
from .similarity_pool_element import SimilarityPoolElement


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


# ## CLASSES

@dataclass
class Post(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    width: int
    height: int
    file_ext: str
    md5: str
    size: int
    illust_urls: List[lambda x: RemoveKeys(x, ['height', 'width'])]
    file_url: str
    sample_url: str
    preview_url: str
    errors: List
    created: datetime.datetime.isoformat

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    file_ext = DB.Column(DB.String(6), nullable=False)
    md5 = DB.Column(DB.String(255), nullable=False)
    size = DB.Column(DB.Integer, nullable=False)
    danbooru_id = DB.Column(DB.Integer, nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    illust_urls = DB.relationship(IllustUrl, secondary=PostIllustUrls, lazy=True, backref=DB.backref('post', uselist=False, lazy=True))
    errors = DB.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete')
    notations = DB.relationship(Notation, secondary=PostNotations, lazy=True, backref=DB.backref('post', uselist=False, lazy=True), cascade='all,delete')
    _pools = DB.relationship(PoolPost, lazy=True, backref=DB.backref('item', lazy=True, uselist=False), cascade='all,delete')
    # uploads <- Upload (MtM)

    # #### Association proxies
    pools = association_proxy('_pools', 'pool')

    # ## Property methods

    @memoized_property
    def has_sample(self):
        return self.width > SAMPLE_DIMENSIONS[0] or self.height > SAMPLE_DIMENSIONS[1] or self.file_ext not in ['jpg', 'png', 'gif']

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
        return os.path.join(IMAGE_DIRECTORY, 'data', self._partial_file_path + self.file_ext)

    @property
    def sample_path(self):
        return os.path.join(IMAGE_DIRECTORY, 'sample', self._partial_file_path + 'jpg') if self.has_sample else self.file_path

    @property
    def preview_path(self):
        return os.path.join(IMAGE_DIRECTORY, 'preview', self._partial_file_path + 'jpg') if self.has_preview else self.file_path

    @memoized_property
    def related_posts(self):
        illust_posts = [illust.posts for illust in self.illusts]
        post_generator = (post for post in itertools.chain(*illust_posts) if post is not None)
        return [post for post in UniqueObjects(post_generator) if post.id != self.id]

    @memoized_property
    def illusts(self):
        return UniqueObjects([illust_url.illust for illust_url in self.illust_urls])

    @memoized_property
    def artists(self):
        return UniqueObjects([illust.artist for illust in self.illusts])

    @memoized_property
    def boorus(self):
        return UniqueObjects(list(itertools.chain(*[artist.boorus for artist in self.artists])))

    @property
    def illust_ids(self):
        return list(set(illust_url.illust_id for illust_url in self.illust_urls))

    @property
    def artist_ids(self):
        return list(set(illust.artist_id for illust in self.illusts))

    @memoized_property
    def similar_pool(self):
        return SimilarityPool.query.filter_by(post_id=self.id).first()

    @property
    def similar_pool_id(self):
        return self.similar_pool.id if self.similar_pool is not None else None

    @memoized_property
    def similar_post_count(self):
        return self._similar_pool_element_query.get_count() if self.similar_pool is not None else 0

    @memoized_property
    def similar_posts(self):
        similar_pool_elements = self._similar_pool_element_query.options(selectinload(SimilarityPoolElement.sibling)).order_by(SimilarityPoolElement.score.desc()).limit(10).all()
        similar_post_ids = [element.post_id for element in similar_pool_elements]
        similar_posts = Post.query.filter(Post.id.in_(similar_post_ids)).all()
        posts = []
        for element in similar_pool_elements:
            data = SimpleNamespace(element=element, pool=self.similar_pool, post=None)
            data.post = next(filter(lambda x: x.id == element.post_id, similar_posts), None)
            posts.append(data)
        return posts

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
        return SimilarityPoolElement.query.filter(SimilarityPoolElement.pool_id == self.similar_pool_id)

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

    basic_attributes = ['id', 'width', 'height', 'size', 'file_ext', 'md5', 'danbooru_id', 'created']
    relation_attributes = ['illust_urls', 'uploads', 'notations', 'errors']
    searchable_attributes = basic_attributes + relation_attributes
