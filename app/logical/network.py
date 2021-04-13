# APP/LOGICAL/NETWORK.PY

# ##PYTHON IMPORTS
import time
import requests


# ##FUNCTIONS

def NetworkQuery(request_url, headers, timeout):
    try:
        response = requests.get(request_url, headers=headers, timeout=timeout)
    except requests.exceptions.ReadTimeout:
        print("\nDownload timed out!")
        return False
    except Exception as e:
        print("Unexpected error:", e)
        return e
    return response


def CheckHTTPResponse(response):
    if response.status_code == 200:
        return True
    if response.status_code >= 500 and response.status_code < 600:
        print("Server Error! Sleeping 5 seconds...")
        time.sleep(5)
    print("HTTP %d - %s" % (response.status_code, response.reason))
    return False


def GetHTTPFile(serverfilepath, headers=None, timeout=10):
    headers = headers if headers is not None else {}
    for i in range(3):
        response = NetworkQuery(serverfilepath, headers, timeout)
        if response is False:
            continue
        if not isinstance(response, requests.Response):
            return response
        if CheckHTTPResponse(response):
            return response.content
    return response
