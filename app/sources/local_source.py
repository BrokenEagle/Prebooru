# APP/SOURCES/LOCAL_SOURCE.PY

# ## PYTHON IMPORTS
import requests

# ## LOCAL IMPORTS
from ..config import WORKER_PORT, SIMILARITY_PORT


# ## FUNCTIONS

def WorkerCheckUploads():
    try:
        requests.get('http://127.0.0.1:%d/check_uploads' % WORKER_PORT, timeout=2)
    except Exception as e:
        return {'error': True, 'message': "Unable to contact worker server: %s" % str(e)}
    return {'error': False}


def SimilarityCheckPosts():
    try:
        requests.get('http://127.0.0.1:%d/check_posts' % SIMILARITY_PORT, timeout=2)
    except Exception as e:
        return {'error': True, 'message': "Unable to contact similarity server: %s" % str(e)}
    return {'error': False}


def SimilarityRegeneratePost(post_id):
    data = {
        'post_ids': [post_id],
    }
    try:
        resp = requests.post('http://127.0.0.1:%d/generate_similarity.json' % SIMILARITY_PORT, json=data, timeout=5)
    except Exception as e:
        return {'error': True, 'message': "Unable to contact similarity server: %s" % str(e)}
    if resp.status_code != 200:
        return {'error': True, 'message': "Similarity server - HTTP %d: %s" % (resp.status_code, resp.reason)}
    return resp.json()
