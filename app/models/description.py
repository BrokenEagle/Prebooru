# APP/MODELS/DESCRIPTION.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class Description(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)

    # ## Class properties

    basic_attributes = ['id', 'body']
    searchable_attributes = basic_attributes
    json_attributes = basic_attributes
