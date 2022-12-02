# APP/HELPERS/NOTATIONS_HELPERS.PY

# ## PYTHON IMPORTS
import re
import html

# ## EXTERNAL IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from app.models.pool_element import PoolElementType


# ## FUNCTIONS

# #### Format functions

def body_excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return html.escape(lines[0][:50]) + ('...' if len(lines[0]) > 50 else '')
