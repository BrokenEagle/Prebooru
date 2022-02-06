# PREBOORU.PY

import logging
logging.root.setLevel(logging.INFO)

# ## PYTHON IMPORTS
import os
import atexit
import colorama
from flask_migrate import Migrate
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app import PREBOORU_APP, DB, SCHEDULER
from app import controllers
from app import helpers
from app.logical.file import load_default, put_get_json
from app.logical.validate import validate_version, validate_integrity
from app.config import DATA_DIRECTORY, PREBOORU_PORT, DEBUG_MODE, VERSION, HAS_EXTERNAL_IMAGE_SERVER

# ## GLOBAL VARIABLES

SERVER_PID_FILE = os.path.join(DATA_DIRECTORY, 'prebooru-server-pid.json')
SERVER_PID = next(iter(load_default(SERVER_PID_FILE, [])), None)

# Registering this with the Prebooru app so that DB commands can be executed with flask
# The environment variables need to be set for this to work, which can be done by executing
# the setup.bat script, then running "flask db" will show all of the available commands.
migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841


# ## FUNCTIONS

@atexit.register
def cleanup():
    if SERVER_PID is not None:
        put_get_json(SERVER_PID_FILE, 'w', [])
    if SCHEDULER.running:
        SCHEDULER.shutdown()


def start_server(args):
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
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    if args.title:
        os.system('title Prebooru Server')
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        import app
        app.MAIN_PROCESS = True
        # Scheduled tasks must be added only after everything else has been initialized
        from app.logical.tasks import schedule  # noqa: F401
        validate_version()
        validate_integrity()
        print("\n========== Starting server - Prebooru-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        put_get_json(SERVER_PID_FILE, 'w', [SERVER_PID])
    PREBOORU_APP.name = 'prebooru'
    SCHEDULER.start()
    if args.public:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT, host="0.0.0.0")
    else:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT)


def init_db(args):
    check = input("This will destroy any existing information. Proceed (y/n)? ")
    if check.lower() != 'y':
        return
    from app.logical.file import create_directory
    from app.config import DB_PATH
    if args.new:
        if os.path.exists(DB_PATH):
            print("Deleting prebooru database!")
            os.remove(DB_PATH)

    print("Creating tables")
    from app.models import NONCE  # noqa: F401, F811
    create_directory(DB_PATH)
    DB.drop_all()
    DB.create_all()

    print("Setting current migration to HEAD")
    from flask_migrate import stamp
    migrate.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        stamp()


def main(args):
    switcher = {
        'server': start_server,
        'init': init_db,
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
PREBOORU_APP.register_blueprint(controllers.api_data.bp)
PREBOORU_APP.register_blueprint(controllers.archive_data.bp)
PREBOORU_APP.register_blueprint(controllers.media_file.bp)
PREBOORU_APP.register_blueprint(controllers.proxy.bp)
PREBOORU_APP.register_blueprint(controllers.static.bp)
PREBOORU_APP.register_blueprint(controllers.similarity.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool_element.bp)
if not HAS_EXTERNAL_IMAGE_SERVER:
    PREBOORU_APP.register_blueprint(controllers.images.bp)

PREBOORU_APP.jinja_env.globals.update(helpers=helpers)
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.do')
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.loopcontrols')


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('type', choices=['init', 'server'])
    parser.add_argument('--new', required=False, default=False, action="store_true",
                        help="Start with a new database file.")
    parser.add_argument('--extension', required=False, default=False, action="store_true",
                        help="Enable Chrome extension.")
    parser.add_argument('--logging', required=False, default=False, action="store_true",
                        help="Display the SQL commands.")
    parser.add_argument('--title', required=False, default=False, action="store_true",
                        help="Adds server title to console window.")
    parser.add_argument('--public', required=False, default=False, action="store_true",
                        help="Makes the server visible to other computers.")
    args = parser.parse_args()
    main(args)
