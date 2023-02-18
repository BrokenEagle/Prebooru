# APP/MODELS/NOTATION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from .pool_element import PoolNotation
from .base import JsonModel, EpochTimestamp


# ## CLASSES

class Notation(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    booru_id = DB.Column(DB.Integer, DB.ForeignKey('booru.id'), nullable=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    no_pool = DB.Column(DB.Boolean, nullable=False)

    # ## Relationships
    _pool = DB.relationship(PoolNotation, lazy=True, uselist=False, cascade='all,delete',
                            backref=DB.backref('item', lazy=True, uselist=False))
    # (MtO) artist [Artist]
    # (MtO) illust [Illust]
    # (MtO) post [Post]

    # ## Association proxies
    pool = association_proxy('_pool', 'pool')

    # ## Instance properties

    @property
    def append_item(self):
        return self.booru or self.artist or self.illust or self.post or (self._pool if not self.no_pool else None)

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
