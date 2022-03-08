# APP/LOGICAL/NETWORK.PY

# ## PYTHON IMPORTS
import time
import requests


# ## FUNCTIONS

def get_http_file(serverfilepath, headers=None, timeout=10):
    headers = headers if headers is not None else {}
    for i in range(3):
        try:
            response = requests.get(serverfilepath, headers=headers, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            return "Unexpected error: %s" % str(e)
        if response.status_code == 200:
            return response.content
        if response.status_code >= 500 and response.status_code < 600:
            time.sleep(5)
            continue
    return "HTTP %d - %s" % (response.status_code, response.reason)
