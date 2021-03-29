# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import time
import atexit
import threading
from flask import Flask, request, jsonify, abort
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
try:
    from app.config import workingdirectory
except ImportError:
    print("Must set the config file first before running. Refer to the readme file.")
    exit(-1)

from app.logical.file import TouchFile
import app.database as DB
from app.sources import SOURCES

# ## GLOBAL VARIABLES

LOCK_FILE = workingdirectory + 'prebooru-lock.txt'
sched = None

# ### INITIALIZATION

app = Flask(__name__)  # See if I can rename this
SUBSCRIPTION_SEMAPHORE = threading.Semaphore()

DB.local.LoadDatabase()
DB.pixiv.LoadDatabase()

# ## FUNCTIONS

#    Auxiliary


def CheckParams(request):
    if 'user_id' not in request.args or not request.args['user_id'].isdigit():
        return "No user ID present!"
    if 'url' not in request.args:
        return "No URL present!"
    return int(request.args['user_id'])


def UploadCheck(request_url):
    for source in SOURCES:
        type, illust_id = source.UploadCheck(request_url)
        if type is not None:
            return source, type, illust_id
    return "Not a valid URL!", None, None


def SubscriptionCheck(request_url):
    for source in SOURCES:
        artist_id = source.SubscriptionCheck(request_url)
        if artist_id is not None:
            return source, artist_id
    return "Not a valid URL!", None


def ShowIDCheck(database, table, id):
    item = database.FindByID(table, id)
    if item is None:
        abort(404)
    return item


#   Routes


@app.route('/uploads', methods=['GET'])
def uploads():
    return jsonify(DB.local.DATABASE['uploads'][::-1])


@app.route('/uploads/<int:id>')
def upload(id):
    return ShowIDCheck(DB.local, 'uploads', id)


@app.route('/posts', methods=['GET'])
def posts():
    return jsonify(DB.local.DATABASE['posts'][::-1])


@app.route('/posts/<int:id>')
def post(id):
    return ShowIDCheck(DB.local, 'posts', id)


@app.route('/subscriptions', methods=['GET'])
def subscriptions():
    return jsonify(DB.local.DATABASE['subscriptions'][::-1])


@app.route('/subscription/<int:id>')
def subscription(id):
    return ShowIDCheck(DB.local, 'subscriptions', id)


@app.route('/illusts', methods=['GET'])
def illusts():
    return jsonify(DB.pixiv.DATABASE['illusts'][::-1])


@app.route('/illusts/<int:id>')
def illust(id):
    return ShowIDCheck(DB.pixiv, 'illusts', id)


@app.route('/artists', methods=['GET'])
def artists():
    return jsonify(DB.pixiv.DATABASE['artists'][::-1])


@app.route('/artists/<int:id>')
def artist(id):
    return ShowIDCheck(DB.pixiv, 'artists', id)


@app.route('/create_upload', methods=['POST', 'GET'])
def create_upload():
    user_id = CheckParams(request)
    if isinstance(user_id, str):
        return user_id
    upload_source, type, illust_id = UploadCheck(request.args['url'])
    if type is None:
        return upload_source
    upload = DB.local.CreateUpload(type, user_id, request_url=request.args['url'])
    threading.Thread(target=upload_source.DownloadIllust, args=(illust_id, upload, type, upload_source)).start()
    return upload


@app.route('/create_subscription', methods=['POST', 'GET'])
def create_subscription():
    user_id = CheckParams(request)
    if isinstance(user_id, str):
        return user_id
    subscription_source, artist_id = SubscriptionCheck(request.args['url'])
    if artist_id is None:
        return subscription_source
    if artist_id in DB.local.SUBSCRIPTION_ARTIST_ID_INDEX:
        subscription = DB.local.SUBSCRIPTION_ARTIST_ID_INDEX[artist_id]
    else:
        subscription = DB.local.CreateSubscription(artist_id, subscription_source.SITE_ID, user_id)
    threading.Thread(target=subscription_source.DownloadArtist, args=(subscription, SUBSCRIPTION_SEMAPHORE, subscription_source)).start()
    return subscription


#   MISC


def CheckSubscriptions():
    pending_subscription = next(filter(lambda x: x['expires'] != 0 and x['expires'] < time.time(), DB.local.DATABASE['subscriptions']), None)
    if pending_subscription is not None:
        subscription_source = SOURCES[pending_subscription['site_id']]
        threading.Thread(target=subscription_source.DownloadArtist, args=(pending_subscription, SUBSCRIPTION_SEMAPHORE)).start()
    else:
        print("No subscriptions to handle...")


@atexit.register
def Cleanup():
    if sched is not None:
        sched.shutdown()
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# ##EXECUTION START

if __name__ == 'prebooru' and not os.path.exists(LOCK_FILE):
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(CheckSubscriptions, 'interval', seconds=15)
    sched.start()
    TouchFile(LOCK_FILE)

if __name__ == '__main__':
    app.run(threaded=True)
