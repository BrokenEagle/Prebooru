# APP\HELPERS\SIMILARITY_HELPER.PY

# ## LOCAL IMPORTS
from ..storage import CacheNetworkUrlpath


# ## FUNCTIONS

def CacheUrl(md5):
    return CacheNetworkUrlpath() + md5 + '.jpg'


def FormClass(similarity_results):
    return "hidden" if similarity_results is not None else None
