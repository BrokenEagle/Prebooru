# APP/MODELS/DESCRIPTION.PY

# ## LOCAL IMPORTS
from .. import SESSION
from .base import JsonModel, integer_column, text_column


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
    id = integer_column(primary_key=True)
    body = text_column(nullable=False)
