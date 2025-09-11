# APP/HELPERS/ILLUST_URLS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import PREVIEW_DIMENSIONS

# ## LOCAL IMPORTS
from .base_helper import general_link, render_tag, get_preview_dimensions, post_link


# ## FUNCTIONS

# #### Link functions

# ###### SHOW

def upload_media_link(text, illust_url):
    return general_link(text, url_for('upload.new_html', illust_url_id=illust_url.id))


def download_media_link(text, illust_url):
    return post_link(text, url_for('illust_url.download_html', id=illust_url.id))


def preview_link(illust_url, lazyload=False):
    preview_width, preview_height = get_preview_dimensions(illust_url.width, illust_url.height, PREVIEW_DIMENSIONS)
    addons = {
        'width': preview_width,
        'height': preview_height,
        'alt': illust_url.shortlink,
        'data-src': illust_url.preview_url,
    }
    if not lazyload:
        addons['src'] = illust_url.preview_url
    return render_tag('img', None, addons)


def image_link(illust_url):
    return render_tag('img', None, {'src': illust_url.full_url, 'alt': illust_url.shortlink})
