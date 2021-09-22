# APP/HELPERS/ILLUST_URLS_HELPERS.PY

# ##PYTHON IMPORTS
from flask import url_for

# ##LOCAL IMPORTS
from .base_helper import general_link


# ##FUNCTIONS

def illust_link(illust_url):
    link_text = 'illust #%d' % illust_url.illust_id
    link_url = url_for('illust.show_html', id=illust_url.illust_id)
    return general_link(link_text, link_url)
