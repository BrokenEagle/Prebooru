# APP/CONFIG.PY

# flake8: noqa

from .default_config import *

try:
    from .local_config import *
except ImportError:
    print("Create an 'app\\local_config.py' file to overwrite the default config.\nUseful for placing information that shouldn't be tracked (e.g. passwords)")
