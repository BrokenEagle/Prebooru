# APP/HELPERS/ILLUST_URLS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

# ###### SHOW

def upload_media_link(text, illust_url):
    return general_link(text, url_for('upload.new_html', illust_url_id=illust_url.id))


def redownload_post_link(text, illust_url):
    return general_link(text, url_for('illust_url.redownload_html', id=illust_url.id), method='POST')
