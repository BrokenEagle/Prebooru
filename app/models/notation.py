# APP/MODELS/NOTATION.PY

# ##PYTHON IMPORTS
import datetime
from dataclasses import dataclass
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel
from .pool_element import PoolNotation


# ##GLOBAL VARIABLES

@dataclass
class Notation(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    body: str
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    _pool = DB.relationship(PoolNotation, lazy=True, uselist=False, cascade='all,delete', backref=DB.backref('item', lazy=True, uselist=False))
    # artist <- Artist (MtO)
    # illust <- Illust (MtO)
    # post <- Post (MtO)

    # #### Association proxies
    pool = association_proxy('_pool', 'pool')

    # ## Property methods

    @property
    def append_item(self):
        return self.pool or self.artist or self.illust or self.post

    @property
    def append_type(self):
        return self.append_item.__table__.name if self.append_item is not None else None

    # #### Private

    @property
    def _pools(self):
        return [self._pool]

    # ## Class properties

    searchable_attributes = ['id', 'body', 'created', 'updated', 'artist', 'illust', 'post']
