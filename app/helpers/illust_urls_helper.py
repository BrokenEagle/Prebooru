# APP/HELPERS/ILLUST_URLS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

# ###### SHOW

def edit_video_links(video_illust_url, sample_illust_url):
    links = []
    if video_illust_url is not None:
        links.append(general_link('video', video_illust_url.edit_url))
    if sample_illust_url is not None:
        links.append(general_link('sample', sample_illust_url.edit_url))
    return Markup(' | ').join(links)


def upload_media_link(text, illust_url):
    return general_link(text, url_for('upload.new_html', illust_url_id=illust_url.id))
