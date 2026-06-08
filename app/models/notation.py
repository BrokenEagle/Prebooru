# APP/MODELS/NOTATION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.data import is_string

# ## LOCAL IMPORTS
from .. import DB
from .pool_element import PoolElement
from .base import JsonModel, integer_column, text_column, boolean_column, timestamp_column, relationship, backref,\
    validate_attachment_json


# ## GLOBAL VARIABLES

NOTATIONS_JSON_DATATYPES = {
    'body': is_string,
    'created': is_string,
    'updated': is_string
}


# ## FUNCTIONS

@property
def notations_json(self):
    if self.notations is None:
        return []
    return [{'body': notation[0], 'created': notation[1], 'updated': notation[2]} for notation in self.notations]


@notations_json.setter
def notations_json(self, values):
    if values is None:
        self.notations = None
    else:
        self.notations = validate_attachment_json(values, NOTATIONS_JSON_DATATYPES)

def check_append(func):
    def wrapper(*args):
        if args[0].append_type is None:
            return None
        return func(*args)
    return wrapper


# ## CLASSES

class Notation(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    body = text_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)
    subscription_id = integer_column(foreign_key='subscription.id', nullable=True)
    booru_id = integer_column(foreign_key='booru.id', nullable=True)
    artist_id = integer_column(foreign_key='artist.id', nullable=True)
    illust_id = integer_column(foreign_key='illust.id', nullable=True)
    post_id = integer_column(foreign_key='post.id', nullable=True)
    no_pool = boolean_column(nullable=False)

    # ## Relationships
    pool_element = relationship(PoolElement, uselist=False, cascade='all,delete',
                                backref=backref('notation', uselist=False))
    # (MtO) subscription [Subscription]
    # (MtO) booru [Booru]
    # (MtO) artist [Artist]
    # (MtO) illust [Illust]
    # (MtO) post [Post]

    # ## Association proxies
    pool = association_proxy('pool_element', 'pool')

    # ## Instance properties

    @property
    def append_type(self):
        if self.subscription_id is not None:
            return 'subscription'
        if self.booru_id is not None:
            return 'booru'
        if self.artist_id is not None:
            return 'artist'
        if self.illust_id is not None:
            return 'illust'
        if self.post_id is not None:
            return 'post'
        if self.no_pool:
            return 'pool_element'

    @memoized_property
    @check_append
    def append_item(self):
        return getattr(self, self.append_type)

    @property
    @check_append
    def append_shortlink(self):
        return getattr(self, self.append_type + '_shortlink')

    @property
    @check_append
    def append_show_url(self):
        return getattr(self, self.append_type + '_show_url')

    @property
    @check_append
    def append_show_link(self):
        return getattr(self, self.append_type + '_show_link')

    # ## Private

    @property
    def pool_elements(self):
        # All other pool elements are MtM, so there needs to be a plural property
        return [self.pool_element]

    __table_args__ = (
        DB.CheckConstraint("no_pool = 0 or no_pool = 1", name="no_pool_boolean"),
        DB.CheckConstraint(
            "((post_id IS NULL) + (illust_id IS NULL) + (artist_id IS NULL) + (booru_id IS NULL) + no_pool) in (4, 5)",
            name="attachments"),
    )


# ## INITIALIZATION

def initialize():
    DB.Index(None, Notation.booru_id, unique=False, sqlite_where=Notation.booru_id.is_not(None))
    DB.Index(None, Notation.artist_id, unique=False, sqlite_where=Notation.artist_id.is_not(None))
    DB.Index(None, Notation.illust_id, unique=False, sqlite_where=Notation.illust_id.is_not(None))
    DB.Index(None, Notation.post_id, unique=False, sqlite_where=Notation.post_id.is_not(None))
    DB.Index(None, Notation.subscription_id, unique=False, sqlite_where=Notation.subscription_id.is_not(None))

    from .subscription import Subscription
    from .booru import Booru
    from .artist import Artist
    from .illust import Illust
    from .post import Post
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.notations.property._configure_started
    Booru.notations.property._configure_started
    Artist.notations.property._configure_started
    Illust.notations.property._configure_started
    Post.notations.property._configure_started
    PoolElement.notation.property._configure_started
    Notation.set_relation_properties()
