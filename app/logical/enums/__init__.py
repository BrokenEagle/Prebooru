# APP/LOGICAL/ENUMS/__INIT__.PY

# ## LOCAL IMPORTS
from .default import *

try:
    from .local import *
except ImportError:
    pass
