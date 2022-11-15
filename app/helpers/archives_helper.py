# APP/HELPERS/ARCHIVES_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import PREVIEW_DIMENSIONS
from utility.data import readable_bytes

# ## LOCAL IMPORTS
from .base_helper import general_link, render_tag, get_preview_dimensions


# ## FUNCTIONS

def archive_preview_link(archive, lazyload):
    return render_tag('a', post_preview_link(archive, lazyload), {'href': archive.show_url})


def post_preview_link(archive, lazyload=False):
    post_data = archive.data['body']
    width = archive.data['body']['width']
    height = archive.data['body']['height']
    preview_width, preview_height = get_preview_dimensions(width, height, PREVIEW_DIMENSIONS)
    file_ext = archive.data['body']['file_ext']
    size = archive.data['body']['size']
    addons = {
        'width': preview_width,
        'height': preview_height,
        'title': f"( {width} x {height} ) : {file_ext.upper()} @ {readable_bytes(size)}",
        'alt': archive.shortlink,
        'data-src': archive.preview_url,
        'onerror': 'Prebooru.onImageError(this)',
    }
    if not lazyload:
        addons['src'] = preview_url
    return render_tag('img', None, addons)


def post_file_link(archive):
    post_data = archive.data['body']
    addons = {
        'width': post_data['width'],
        'height': post_data['height'],
        'alt': archive.shortlink,
        'src': archive.file_url,
    }
    return render_tag('img', None, addons)


def post_video_link(archive):
    post_data = archive.data['body']
    addons = {
        'width': post_data['width'],
        'height': post_data['height'],
        'controls': None,
        'alt': archive.shortlink,
        'src': archive.file_url,
    }
    return render_tag('video', True, addons)


def reinstantiate_item_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Recreate", url_for('archive.reinstantiate_item_html', id=archive.id), **addons)


def relink_item_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Relink", url_for('archive.relink_item_html', id=archive.id), **addons)


def set_permenant_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Unexpire", url_for('archive.set_permenant_html', id=archive.id), **addons)


def set_temporary_link(archive):
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Expire", url_for('archive.set_temporary_html', id=archive.id), **addons)


def has_relink(archive):
    for key in archive.data['links']:
        if len(archive.data['links'][key]) > 0:
            return True
    return False
