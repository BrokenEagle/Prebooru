# APP/LOGICAL/NETWORK.PY

# ## PYTHON IMPORTS
import time
import json
import httpx

# ## PACKAGE IMPORTS
from config import PREBOORU_PORT


# ## FUNCTIONS

def get_http_data(serverfilepath, method='get', **args):
    if 'timeout' not in args:
        args['timeout'] = 10
    request_method = getattr(httpx, method)
    response = None
    for i in range(4):
        try:
            response = request_method(serverfilepath, **args)
        except httpx.ConnectTimeout:
            continue
        except Exception as e:
            return "Unexpected error: %s" % str(e)
        if response.status_code == 200:
            return response.content
        if response.status_code >= 500 and response.status_code < 600:
            print("Server error; sleeping...")
            time.sleep(15)
            continue
    if response is not None:
        return "HTTP %d - %s" % (response.status_code, response.reason)
    else:
        return "Repeated connection timeouts"


def send_prebooru_request(path, method, **args):
    send_url = f'http://127.0.0.1:{PREBOORU_PORT}' + path
    return get_http_data(send_url, method=method, **args)


def prebooru_json_request(path, method, **args):
    content = send_prebooru_request(path, method, **args)
    if isinstance(content, str):
        return content
    elif isinstance(content, bytes):
        try:
            data = json.loads(content)
        except Exception as e:
            return "Unable to read request [%s]: %s" % (str(e), content)
        if data.get('error') is True:
            return data['message']
        return data
    else:
        return "Unrecognized response."
