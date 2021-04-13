# APP/HELPERS/UPLOADS_HELPER.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for

# ##LOCAL IMPORTS
from .base_helper import SearchUrlFor, GeneralLink


# ## FUNCTIONS

def FormTitleApellation(illust_url):
    return Markup(': <a href="%s">illust #%d</a>' % (url_for('illust.show_html', id=illust_url.illust_id), illust_url.illust_id)) if illust_url is not None else ""


def PostSearch(upload):
    return SearchUrlFor('post.index_html', uploads={'id': upload.id})


def CheckPendingLink():
    return GeneralLink('pending', url_for('upload.upload_check_html'))
