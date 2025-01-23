# APP/MODELS/LABEL.PY

# ## LOCAL IMPORTS
from .. import SESSION
from .base import JsonModel, integer_column, text_column


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
    id = integer_column(primary_key=True)
    name = text_column(nullable=False)
