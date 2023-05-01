# APP/HELPERS/MEDIA_FILES_HELPER.PY

# ## LOCAL IMPORTS
from .base_helper import render_tag


# ## FUNCTIONS

# #### Link functions

# ###### INDEX

def file_link(media_file):
    addons = {
        'alt': media_file.shortlink,
        'src': media_file.media.original_file_url,
        'onerror': 'return Prebooru.onImageError(this)',
    }
    return render_tag('img', None, addons)
