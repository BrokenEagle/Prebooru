# APP/MODELS/UGOIRA.PY

# ## LOCAL IMPORTS
from .. import SESSION
from .base import JsonModel, integer_column, json_column


# ## FUNCTIONS

def ugoira_creator(frames):
    ugoira = Ugoira.query.filter_by(frames=frames).one_or_none()
    if ugoira is None:
        ugoira = Ugoira(frames=frames)
        SESSION.add(ugoira)
        SESSION.flush()
    return ugoira


# ## CLASSES

class Ugoira(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    frames = json_column(nullable=True)
