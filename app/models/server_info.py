# APP/MODELS/SERVER_INFO.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class ServerInfo(JsonModel):
    # ## Public

    field = DB.Column(DB.String(), primary_key=True)
    info = DB.Column(DB.String(), nullable=False)

    @classmethod
    def find(cls, field):
        return cls.query.filter_by(field=field).one_or_none()

    # ## Private

    __table_args__ = (
        {'sqlite_with_rowid': False},
    )
