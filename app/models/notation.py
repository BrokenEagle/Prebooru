# APP/MODELS/NOTATION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from .pool_element import PoolNotation
from .base import JsonModel, integer_column, text_column, boolean_column, timestamp_column, relationship, backref


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
    _pool = relationship(PoolNotation, uselist=False, cascade='all,delete', backref=backref('item', uselist=False))
    # (MtO) artist [Artist]
    # (MtO) illust [Illust]
    # (MtO) post [Post]

    # ## Association proxies
    pool = association_proxy('_pool', 'pool')

    # ## Instance properties

    @property
    def append_item(self):
        return self.subscription or self.booru or self.artist or self.illust or self.post or\
            (self._pool if not self.no_pool else None)

    @property
    def append_type(self):
        return self.append_item.table_name if self.append_item is not None else None

    def attach(self, attr, record):
        if record.table_name == 'pool':
            self.no_pool = False
            record._elements.append(self)
        else:
            self.no_pool = True
            setattr(self, attr, record)

    # ## Class properties

    @classmethod
    def loads(cls, data, *args):
        record = super().loads(data)
        record.no_pool = False
        return record

    archive_excludes = {'no_pool'}

    # ## Private

    @property
    def _pools(self):           # All other pool elements are MtM, so there needs to be a plural property
        return [self._pool]

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
