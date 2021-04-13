# APP/HELPERS/ILLUST_URLS_HELPERS.PY

# ##PYTHON IMPORTS
from flask import url_for

# ##LOCAL IMPORTS
from .base_helper import GeneralLink


# ##FUNCTIONS

def IllustLink(illust_url):
    link_text = 'illust #%d' % illust_url.illust_id
    link_url = url_for('illust.show_html', id=illust_url.illust_id)
    return GeneralLink(link_text, link_url)
