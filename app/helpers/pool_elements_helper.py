# APP/HELPERS/POOL_ELEMENTS_HELPERS.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for


# ## FUNCTIONS

# #### Helper functions

def is_general_form(form):
    return (form.illust_id.data is None) and (form.post_id.data is None) and (form.notation_id.data is None)

