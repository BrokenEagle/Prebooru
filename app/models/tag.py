# APP/MODELS/TAG.PY

# ## EXTERNAL IMPORTS
from flask import Markup
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .. import SESSION
from .model_enums import TagType
from .base import JsonModel, integer_column, text_column, enum_column, register_enum_column


# ## FUNCTIONS

def site_tag_creator(name):
    tag = SiteTag.query.filter_by(name=name).one_or_none()
    if tag is None:
        tag = SiteTag(name=name)
        SESSION.add(tag)
    return tag


def user_tag_creator(name):
    tag = UserTag.query.filter_by(name=name).one_or_none()
    if tag is None:
        tag = UserTag(name=name)
        SESSION.add(tag)
    return tag


# ## CLASSES

class Tag(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    name = text_column(nullable=False)
    type_id = enum_column(foreign_key='tag_type.id', nullable=False)

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
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    # ## Class properties

    @classproperty(cached=True)
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty(cached=False)
    def json_attributes(cls):
        return cls.repr_attributes

    polymorphic_base = True

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': TagType.tag.id,
        'polymorphic_on': type_id,
    }


class SiteTag(Tag):
    # ## Instance properties

    @memoized_property
    def illust_count(self):
        return self._illust_query.distinct_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct_count()

    # ## Class properties

    polymorphic_base = False

    # ## Private

    @property
    def _illust_query(self):
        from .illust import Illust
        return Illust.query.join(Tag, Illust.tags).filter(Tag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        from .illust_url import IllustUrl
        from .illust import Illust
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust).join(Tag, Illust.tags)\
                         .filter(Tag.id == self.id)

    __mapper_args__ = {
        'polymorphic_identity': TagType.site_tag.id,
    }


class UserTag(Tag):
    # ## Instance properties

    @memoized_property
    def illust_count(self):
        return self._illust_query.distinct_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct_count()

    # ## Class properties

    polymorphic_base = False

    # ## Private

    @property
    def _illust_query(self):
        from .illust import Illust
        from .illust_url import IllustUrl
        from .post import Post
        return Illust.query.join(IllustUrl).join(Post, IllustUrl.post).join(UserTag, Post.tags)\
                           .filter(UserTag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        return Post.query.join(UserTag, Post.tags).filter(UserTag.id == self.id)

    __mapper_args__ = {
        'polymorphic_identity': TagType.user_tag.id,
    }


# ## FUNCTIONS

def initialize():
    setattr(Tag, 'polymorphic_classes', [SiteTag, UserTag])
    register_enum_column(Tag, TagType, 'type')
