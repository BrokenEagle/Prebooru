# APP/HELPERS/NOTATIONS_HELPERS.PY

# ## PYTHON IMPORTS
import re
import html

# ## EXTERNAL IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..enum_imports import pool_element_type


# ## FUNCTIONS

# #### Format functions

def body_excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return html.escape(lines[0][:50]) + ('...' if len(lines[0]) > 50 else '')


def edit_append_info(notation):
    if notation.append_type in pool_element_type.names:
        return Markup(f"For {notation.append_item.pool.name_link}:")
    else:
        return Markup(f"For {notation.append_item.show_link}:")
