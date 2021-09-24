# APP/HELPERS/NOTATIONS_HELPERS.PY

# ##PYTHON IMPORTS
import re
import html
from flask import Markup, url_for

# ##LOCAL IMPORTS
from .base_helper import general_link
from . import artists_helper as ARTIST
from . import illusts_helper as ILLUST


# ## FUNCTIONS

# #### Route functions

# ###### INDEX

def body_excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return html.escape(lines[0][:50]) + ('...' if len(lines[0]) > 50 else '')
