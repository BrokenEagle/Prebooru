# APP/MODELS/BOORU.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from .artist import Artist
from .illust import Illust
from .illust_url import IllustUrl
from .post import Post
from .label import Label
from .base import JsonModel, classproperty


# ## GLOBAL VARIABLES

BooruNames = DB.Table(
    'booru_names',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)

BooruArtists = DB.Table(
    'booru_artists',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)


# ## CLASSES

class Booru(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    danbooru_id = DB.Column(DB.Integer, unique=True, nullable=False)
    current_name = DB.Column(DB.String(255), nullable=False)
    banned = DB.Column(DB.Boolean, nullable=False)
    deleted = DB.Column(DB.Boolean, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    _names = DB.relationship(Label, secondary=BooruNames, lazy=True)
    artists = DB.relationship(Artist, secondary=BooruArtists, lazy=True, backref=DB.backref('boorus', lazy=True))

    # #### Association proxies
    names = association_proxy('_names', 'name')
    artist_ids = association_proxy('artists', 'id')

    # ## Property methods

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.distinct(Post.id)
        q = q.order_by(Post.id.desc())
        q = q.limit(10)
        return q.all()

    @memoized_property
    def illust_count(self):
        return self._illust_query.get_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct().relation_count()

    @memoized_property
    def _illust_query(self):
        return Illust.query.join(Artist, Illust.artist).join(Booru, Artist.boorus).filter(Booru.id == self.id)

    @memoized_property
    def _post_query(self):
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(Artist, Illust.artist)\
                   .join(Booru, Artist.boorus).filter(Booru.id == self.id)

    # ## Methods

    def delete(self):
        self._names.clear()
        self.artists.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['names']
