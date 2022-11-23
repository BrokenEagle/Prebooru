# APP/MODELS/VERSION.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class Version(JsonModel):
    # ## Columns
    id = DB.Column(DB.TEXT, primary_key=True)
    ver_num = DB.Column(DB.TEXT, nullable=False)

    __table_args__ = (
        {'sqlite_with_rowid': False},
    )
