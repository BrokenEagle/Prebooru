# APP/HELPERS/NOTATIONS_HELPERS.PY

# ## PYTHON IMPORTS
import re
import html

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from .base_helper import general_link, convert_to_html


# ## GLOBAL VARIABLES

FILEPATH_RG = re.compile(r'^[C-Z]:\\.*(?:jpg|gif|png)$', re.IGNORECASE)


# ## FUNCTIONS

# #### Format functions

def body_excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return html.escape(lines[0][:50]) + ('...' if len(lines[0]) > 50 else '')


def edit_append_info(notation):
    if notation.append_type == 'pool_element':
        return Markup(f"For {notation.append_item.pool.name_link}:")
    else:
        return Markup(f"For {notation.append_item.show_link}:")


def to_html(notation):
    lines = re.split(r'\r?\n', notation.body)
    for i, line in enumerate(lines):
        if FILEPATH_RG.match(line):
            addons = {
                'onclick': 'return Prebooru.copyFileLink(this)',
                'data-file-path': line,
                'title': "Click to copy.", 'class': 'file-link',
            }
            lines[i] = Markup(general_link(line, "#", **addons))
        else:
            lines[i] = convert_to_html(line)
    return Markup("<br>").join(lines)


# #### Link functions

def add_notation_link(notation_key, item_id):
    params = {
        notation_key: item_id,
        'redirect': 'true',
    }
    return general_link("+", url_for('notation.new_html', **params))
