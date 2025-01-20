# APP/MODELS/LABEL.PY

# ## LOCAL IMPORTS
from .. import DB, SESSION
from .base import JsonModel


# ## FUNCTIONS

def label_creator(name):
    label = Label.query.filter_by(name=name).one_or_none()
    if label is None:
        label = Label(name=name)
        SESSION.add(label)
        SESSION.flush()
    return label


# ## CLASSES

class Label(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    # ## Relations
    # (MtM) site_artist_accounts [Artist]
    # (MtM) name_artists [Artist]
    # (MtM) boorus [Booru]
