# APP/MODELS/TAG.PY

# ## EXTERNAL IMPORTS
from flask import Markup
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from ..enums import TagTypeEnum
from .base import JsonModel, IntEnum


# ## CLASSES

class Tag(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)
    type = DB.Column(IntEnum(TagTypeEnum), nullable=False)

    # ## Instance properties

    @property
    def name_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.name))

    @property
    def display_type(self):
        return self.type.name.replace('_', ' ').capitalize()

    @memoized_property
    def recent_posts(self):
        from .post import Post
        q = self._post_query
        q = q.distinct(Post.id)
        q = q.order_by(Post.id.desc())
        q = q.limit(10)
        return q.all()

    # ## Class properties

    polymorphic_base = True
    type_enum = TagTypeEnum

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': TagTypeEnum.tag,
        'polymorphic_on': type,
    }


class SiteTag(Tag):
    # ## Relations
    # (MtM) illusts [Illust]

    # ## Instance properties

    @memoized_property
    def illust_count(self):
        return self._illust_query.get_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct().relation_count()

    # ## Class properties

    polymorphic_base = False

    # ## Private

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

    __mapper_args__ = {
        'polymorphic_identity': TagTypeEnum.site_tag,
    }


class UserTag(Tag):
    # ## Relations
    # (MtM) posts [Post]

    # ## Instance properties

    @memoized_property
    def illust_count(self):
        return self._illust_query.distinct().relation_count()

    @memoized_property
    def post_count(self):
        return self._post_query.get_count()

    # ## Class properties

    polymorphic_base = False

    # ## Private

    @property
    def _illust_query(self):
        from .illust import Illust
        from .illust_url import IllustUrl
        from .post import Post
        return Illust.query.join(IllustUrl).join(Post, IllustUrl.post).join(UserTag, Post._tags)\
                     .filter(UserTag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        return Post.query.join(UserTag, Post._tags).filter(UserTag.id == self.id)

    __mapper_args__ = {
        'polymorphic_identity': TagTypeEnum.user_tag,
    }


# ## FUNCTIONS

def initialize():
    setattr(Tag, 'polymorphic_classes', [SiteTag, UserTag])
