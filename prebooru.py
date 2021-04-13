# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import atexit
import colorama
from flask_migrate import Migrate
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app import PREBOORU_APP, DB
from app import controllers
from app import helpers
from app.logical.file import LoadDefault, PutGetJSON
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, PREBOORU_PORT, DEBUG_MODE, VERSION

# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'prebooru-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

# Registering this with the Prebooru app so that DB commands can be executed with flask
# The environment variables need to be set for this to work, which can be done by executing
# the setup.bat script, then running "flask db" will show all of the available commands.
migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841


# ## FUNCTIONS

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])


def StartServer(args):
    global SERVER_PID
    if SERVER_PID is not None:
        print("Server process already running: %d" % SERVER_PID)
        input()
        exit(-1)
    if args.extension:
        try:
            from flask_flaskwork import Flaskwork
        except ImportError:
            print("Install flaskwork module: pip install flask-flaskwork --upgrade")
        else:
            Flaskwork(PREBOORU_APP)
    if args.title:
        os.system('title Prebooru Server')
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n========== Starting server - Prebooru-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
    PREBOORU_APP.name = 'prebooru'
    if args.public:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT, host="0.0.0.0")
    else:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT)


def InitDB(args):
    check = input("This will destroy any existing information. Proceed (y/n)? ")
    if check.lower() != 'y':
        return
    from app.logical.file import CreateDirectory
    from app.config import DB_PATH, CACHE_PATH, SIMILARITY_PATH
    if args.new:
        if os.path.exists(DB_PATH):
            print("Deleting prebooru database!")
            os.remove(DB_PATH)
        if os.path.exists(CACHE_PATH):
            print("Deleting cache database!")
            os.remove(CACHE_PATH)
        if os.path.exists(SIMILARITY_PATH):
            print("Deleting similarity database!")
            os.remove(SIMILARITY_PATH)

    print("Creating tables")
    from app.models import NONCE  # noqa: F401, F811
    from app.cache import NONCE  # noqa: F401, F811
    from app.similarity import NONCE  # noqa: F401, F811
    CreateDirectory(DB_PATH)
    CreateDirectory(CACHE_PATH)
    CreateDirectory(SIMILARITY_PATH)
    DB.drop_all()
    DB.create_all()

    print("Setting current migration to HEAD")
    from flask_migrate import stamp
    migrate.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        stamp()


def Main(args):
    switcher = {
        'server': StartServer,
        'init': InitDB,
    }
    switcher[args.type](args)


# ### INITIALIZATION

os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'

colorama.init(autoreset=True)

PREBOORU_APP.register_blueprint(controllers.illust.bp)
PREBOORU_APP.register_blueprint(controllers.illust_url.bp)
PREBOORU_APP.register_blueprint(controllers.artist.bp)
PREBOORU_APP.register_blueprint(controllers.artist_url.bp)
PREBOORU_APP.register_blueprint(controllers.booru.bp)
PREBOORU_APP.register_blueprint(controllers.upload.bp)
PREBOORU_APP.register_blueprint(controllers.post.bp)
PREBOORU_APP.register_blueprint(controllers.pool.bp)
PREBOORU_APP.register_blueprint(controllers.pool_element.bp)
PREBOORU_APP.register_blueprint(controllers.tag.bp)
PREBOORU_APP.register_blueprint(controllers.notation.bp)
PREBOORU_APP.register_blueprint(controllers.error.bp)
PREBOORU_APP.register_blueprint(controllers.proxy.bp)
PREBOORU_APP.register_blueprint(controllers.static.bp)
PREBOORU_APP.register_blueprint(controllers.similarity.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool_element.bp)

PREBOORU_APP.jinja_env.globals.update(helpers=helpers)
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.do')
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.loopcontrols')

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('type', choices=['init', 'server'])
    parser.add_argument('--new', required=False, default=False, action="store_true", help="Start with a new database file.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    parser.add_argument('--public', required=False, default=False, action="store_true", help="Makes the server visible to other computers.")
    args = parser.parse_args()
    Main(args)
