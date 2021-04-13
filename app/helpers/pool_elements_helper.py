# APP/HELPERS/POOL_ELEMENTS_HELPERS.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for


# ## FUNCTIONS

# #### Helper functions

def IsGeneralForm(form):
    return (form.illust_id.data is None) and (form.post_id.data is None) and (form.notation_id.data is None)


# ###### NEW/EDIT

def FormHeader(form):
    html_text = "pool element"
    if IsGeneralForm(form):
        return html_text
    html_text += ': '
    if form.illust_id.data is not None:
        html_text += """<a href="%s">illust #%d</a>""" % (url_for('illust.show_html', id=form.illust_id.data), form.illust_id.data)
    elif form.post_id.data is not None:
        html_text += """<a href="%s">post #%d</a>""" % (url_for('post.show_html', id=form.post_id.data), form.post_id.data)
    elif form.notation_id.data is not None:
        html_text += """<a href="%s">notation #%d</a>""" % (url_for('notation.show_html', id=form.notation_id.data), form.notation_id.data)
    return Markup(html_text)
