# APP/MODELS/SERVER_INFO.PY

# ## LOCAL IMPORTS
from .base import JsonModel, text_column


# ## CLASSES

class ServerInfo(JsonModel):
    # ## Public

    field = text_column(primary_key=True)
    info = text_column(nullable=False)

    @classmethod
    def find(cls, field):
        return cls.query.filter_by(field=field).one_or_none()

    # ## Private

    __table_args__ = (
        {'sqlite_with_rowid': False},
    )
