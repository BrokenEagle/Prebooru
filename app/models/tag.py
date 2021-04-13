# APP/MODELS/TAG.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy.util import memoized_property

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##CLASSES

@dataclass
class Tag(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    name: str

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    # ## Property methods

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
        return Illust.query.join(Tag, Illust.tags).filter(Tag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        from .illust_url import IllustUrl
        from .illust import Illust
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust).join(Tag, Illust.tags).filter(Tag.id == self.id)

    # ## Class properties

    searchable_attributes = ['id', 'name']
