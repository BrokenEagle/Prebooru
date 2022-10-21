# APP/MODELS/NOTATION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from .pool_element import PoolNotation
from .base import JsonModel, EpochTimestamp


# ## CLASSES

class Notation(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # #### Relationships
    _pool = DB.relationship(PoolNotation, lazy=True, uselist=False, cascade='all,delete',
                            backref=DB.backref('item', lazy=True, uselist=False))
    # artist <- Artist (MtO)
    # illust <- Illust (MtO)
    # post <- Post (MtO)

    # #### Association proxies
    pool = association_proxy('_pool', 'pool')

    # ## Property methods

    @property
    def append_item(self):
        return self._pool or self.artist or self.illust or self.post

    @property
    def append_type(self):
        return self.append_item.model_name if self.append_item is not None else None

    # #### Private

    @property
    def _pools(self):           # All other pool elements are MtM, so there needs to be a plural property
        return [self._pool]
