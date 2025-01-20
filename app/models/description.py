# APP/MODELS/DESCRIPTION.PY

# ## LOCAL IMPORTS
from .. import DB, SESSION
from .base import JsonModel


# ## FUNCTIONS

def description_creator(body):
    description = Description.query.filter_by(body=body).one_or_none()
    if description is None:
        description = Description(body=body)
        SESSION.add(description)
        SESSION.flush()
    return description


# ## CLASSES

class Description(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)

    # ## Relations
    # (MtM) artists [Artist]
    # (MtM) illusts [Illust]
