# APP/HELPERS/ERRORS_HELPER.PY

# ## PYTHON IMPORTS
import re
import html
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import GeneralLink


# ## GLOBAL VARIABLES

SHORTLINK_RG = re.compile(r'(\w+) #(\d+)')


# ## FUNCTIONS

def FormatMessage(error):
    position = 0
    message = re.sub('\r?\n', '<br>', html.escape(error.message))
    while True:
        match = SHORTLINK_RG.search(message, position)
        if match is None:
            return message
        try:
            show_url = url_for(match.group(1) + '.show_html', id=int(match.group(2)))
            replace = GeneralLink(match.group(0), show_url)
        except Exception as e:
            print("Format message error:", e)
            replace = match.group(0)
        message = message[:match.start()] + replace + message[match.end():]
        position += len(replace)
