# APP/HELPERS/UPLOADS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link, add_container


# ## FUNCTIONS

# #### Uploads

# ###### Form functions

def form_title_apellation(illust_url):
    if illust_url is None:
        return ""
    url = url_for('illust.show_html', id=illust_url.illust_id)
    return Markup(': <a href="%s">illust #%d</a>' % (url, illust_url.illust_id))


# ###### Link functions

def check_pending_link(upload):
    return general_link('pending', url_for('upload.upload_check_html', id=upload.id), method="POST")


def resubmit_link(upload):
    return general_link('error', url_for('upload.resubmit_html', id=upload.id), method="POST")


def post_search_link(upload):
    return general_link('»', search_url_for('post.index_html', uploads={'id': upload.id}))


# ### Upload elements

def element_status(element):
    active = 'active' if element.illust_url.active else 'deprecated'
    return Markup(' ').join([element.status.name.title(),
                             add_container('span', f"({active})", classlist=['small-caps'])])
