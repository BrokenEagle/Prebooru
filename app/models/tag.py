# APP/MODELS/TAG.PY

# ## EXTERNAL IMPORTS
from flask import Markup
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ##CLASSES

class Tag(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    # ## Property methods

    @property
    def name_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.name))

    @memoized_property
    def recent_posts(self):
        from .post import Post
        q = self._post_query
        q = q.order_by(Post.id.desc())
        q = q.limit(10)
        return q.all()

    @memoized_property
    def illust_count(self):
        return self._illust_query.get_count()

    @memoized_property
    def post_count(self):
        return self._post_query.get_count()

    # #### Private

    @property
    def _illust_query(self):
        from .illust import Illust
        return Illust.query.join(Tag, Illust._tags).filter(Tag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        from .illust_url import IllustUrl
        from .illust import Illust
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust).join(Tag, Illust._tags)\
                   .filter(Tag.id == self.id)

    # ## Class properties

    basic_attributes = ['id', 'name']
    searchable_attributes = basic_attributes
    json_attributes = basic_attributes
