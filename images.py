# IMAGES.PY

# ## PYTHON IMPORTS
import os
import sys
import atexit
from argparse import ArgumentParser
from flask import Flask, send_from_directory

# ## LOCAL IMPORTS
from app.logical.file import LoadDefault, PutGetJSON
from app.storage import IMAGE_DIRECTORY
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, IMAGE_PORT, DEBUG_MODE, VERSION


# #### Python Check

if sys.version_info.major == 3 and sys.version_info.minor < 7:
    print("Python version must be at least 3.7 to run this application.")
    exit(-1)


# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'images-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

IMAGES_APP = Flask(__name__)
IMAGES_APP.config.from_mapping(
    DEBUG=DEBUG_MODE,
)

# ## FUNCTIONS

# #### Route functions

@IMAGES_APP.route('/<path:path>')
def send_file(path):
    return send_from_directory(IMAGE_DIRECTORY, path)


# #### Initialization

os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])


# #### Main execution functions

def StartServer(args):
    global SERVER_PID
    if SERVER_PID is not None:
        print("\nServer process already running: %d" % SERVER_PID)
        input()
        exit(-1)
    if args.title:
        os.system('title Image Server')
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n========== Starting server - Images-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
    if args.public:
        IMAGES_APP.run(threaded=True, port=IMAGE_PORT, host="0.0.0.0")
    else:
        IMAGES_APP.run(threaded=True, port=IMAGE_PORT)


# ## EXECUTION START

if __name__ == "__main__":
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    parser.add_argument('--public', required=False, default=False, action="store_true", help="Makes the server visible to other computers.")
    args = parser.parse_args()
    StartServer(args)
