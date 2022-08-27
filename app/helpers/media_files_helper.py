# APP/HELPERS/MEDIA_FILES_HELPER.PY

# ## LOCAL IMPORTS
from .base_helper import general_link, render_tag, get_preview_dimensions


# ## FUNCTIONS

# #### Link functions

# ###### INDEX

def file_link(media_file):
    addons = {
        'alt': media_file.shortlink,
        'src': media_file.file_url,
        'onerror': 'return Prebooru.onImageError(this)',
    }
    return render_tag('img', None, addons)
