# APP/HELPERS/DOWNLOADS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link, add_container


# ## FUNCTIONS

# #### Downloads

# ###### Link functions

def check_pending_link(download):
    return general_link('pending', url_for('download.download_check_html', id=download.id), method="POST")


def resubmit_link(download):
    return general_link('error', url_for('download.resubmit_html', id=download.id), method="POST")


def post_search_link(download):
    return general_link('»', search_url_for('post.index_html', downloads={'id': download.id}))


# #### Download elements

def element_status(element):
    active = 'active' if element.illust_url.active else 'deprecated'
    return Markup(' ').join([element.status.name.title(),
                             add_container('span', f"({active})", classlist=['small-caps'])])
