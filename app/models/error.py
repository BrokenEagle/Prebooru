# APP/MODELS/ERROR.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, NormalizedDatetime


# ## CLASSES

class Error(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    module = DB.Column(DB.String(255), nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(NormalizedDatetime(), nullable=False)

    @memoized_property
    def append_item(self):
        return self.upload or self.upload_element or self.post or self.subscription or self.subscription_element
