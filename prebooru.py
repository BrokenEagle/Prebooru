# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import time

# ## GLOBAL VARIABLES

MAX_MEMORY_MB = 800
POLLING_INTERVAL = 5
SHUTDOWN_ERROR_FILE = 'prebooru-shutdown-error.txt'


# ## FUNCTIONS

# #### Initialization functions

def initialize_server(args):
    global PREBOORU_APP, SCHEDULER, load_default, put_get_json, validate_version, validate_integrity
    from app import PREBOORU_APP, SCHEDULER
    from app.logical.validate import validate_version, validate_integrity
    initialize_environment()
    initialize_controllers()
    initialize_helpers()
    initialize_server_callbacks(args)


def initialize_environment():
    import colorama
    os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'
    colorama.init(autoreset=True)


def initialize_helpers():
    from app import helpers
    PREBOORU_APP.jinja_env.globals.update(helpers=helpers)
    PREBOORU_APP.jinja_env.add_extension('jinja2.ext.do')
    PREBOORU_APP.jinja_env.add_extension('jinja2.ext.loopcontrols')


def initialize_controllers():
    from app import controllers
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


def initialize_server_callbacks(args):
    import atexit
    from flask import request
    from app import SERVER_INFO

    @atexit.register
    def cleanup(expected_requests=0):
        if SERVER_PID is not None:
            put_get_json(SERVER_PID_FILE, 'w', [])
        if SCHEDULER.running:
            print("Shutting down scheduler...")
            SCHEDULER.shutdown()
        # Wait some to allow current requests to complete
        print("Checking active requests...")
        iterations = 0
        while True:
            if SERVER_INFO.active_requests <= expected_requests or iterations >= 8:
                return
            print("Waiting for active requests to complete.")
            iterations += 1
            time.sleep(1)

    if args.unique_id is not None:
        SERVER_INFO.unique_id = args.unique_id

        @PREBOORU_APP.route('/shutdown', methods=['POST'])
        def shutdown():
            uid = request.args.get('uid')
            # Only allow shutdowns from localhost
            if SERVER_INFO.addr == '127.0.0.1' and uid == SERVER_INFO.unique_id:
                print("Shutting down...")
                SERVER_INFO.allow_requests = False
                cleanup(1)
                return {'error': False}
            else:
                print("Invalid shutdown request.")
                return {'error': True, 'message': "This route is only available from the watchdog."}


def initialize_migrate():
    global PREOBOORU_MIGRATE
    from flask_migrate import Migrate
    # Registering this with the Prebooru app so that DB commands can be executed with flask
    # The environment variables need to be set for this to work, which can be done by executing
    # the setup.bat script, then running "flask db" will show all of the available commands.
    PREOBOORU_MIGRATE = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841


# #### Main execution functions

def start_server(args):
    global SERVER_PID, SERVER_PID_FILE, DATA_DIRECTORY, PREBOORU_PORT, DEBUG_MODE, VERSION, HAS_EXTERNAL_IMAGE_SERVER,\
        load_default, put_get_json
    from app.config import DATA_DIRECTORY, PREBOORU_PORT, DEBUG_MODE, VERSION, HAS_EXTERNAL_IMAGE_SERVER
    from app.logical.file import load_default, put_get_json
    SERVER_PID_FILE = os.path.join(DATA_DIRECTORY, 'prebooru-server-pid.json')
    SERVER_PID = next(iter(load_default(SERVER_PID_FILE, [])), None)
    if SERVER_PID is not None:
        print("Server process already running: %d" % SERVER_PID)
        exit(-1)
    initialize_server(args)
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
    initialize_migrate()
    PREOBOORU_MIGRATE.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        stamp()


def server_watchdog(args):
    watchdog_info = {}
    try:
        watchdog_loop(watchdog_info)
    except KeyboardInterrupt:
        print("Exiting program")
        shutdown_server(watchdog_info['proc'], watchdog_info['unique_id'])
        exit(-1)


def kill_server(args):
    import psutil
    from app.config import DATA_DIRECTORY
    from app.logical.file import load_default, put_get_json
    SERVER_PID_FILE = os.path.join(DATA_DIRECTORY, 'prebooru-server-pid.json')
    SERVER_PID = next(iter(load_default(SERVER_PID_FILE, [])), None)
    if SERVER_PID is None:
        print("No prebooru server is currently running.")
        return
    try:
        proc = psutil.Process(int(SERVER_PID))
    except psutil.NoSuchProcess:
        print(f"No server found with PID {SERVER_PID}.")
    else:
        print("Killing server...")
        shutdown_server(proc)
    finally:
        put_get_json(SERVER_PID_FILE, 'w', [])


# #### Auxiliary functions

def watchdog_loop(watchdog_info):
    import sys
    import uuid
    import psutil
    import subprocess
    from werkzeug._reloader import _get_args_for_reloading

    WERKZEUG_RESTART_CODE = 3
    MAX_MEMORY = int(os.environ.get('PREBOORU_MAX_MEMORY', MAX_MEMORY_MB * (1024 * 1024)))
    new_environ = os.environ.copy()
    errorcode = WERKZEUG_RESTART_CODE
    last_checked = time.time()
    while True:
        if errorcode == WERKZEUG_RESTART_CODE:
            unique_id = watchdog_info['unique_id'] = str(uuid.uuid4())
            process_arguments = [sys.executable, 'prebooru.py', 'server', '--unique-id', unique_id] +\
                _get_args_for_reloading()[3:]
            process_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            p = subprocess.Popen(process_arguments, env=new_environ, close_fds=False, creationflags=process_flags)
            watchdog_info['proc'] = proc = psutil.Process(p.pid)
        elif errorcode is not None:
            exit(errorcode)
        errorcode = p.returncode and (p.returncode if (p.returncode < (1 << 31)) else (p.returncode - (1 << 32)))
        time.sleep(POLLING_INTERVAL)
        if ((time.time() - last_checked) < 300):  # Only check the memory every 5 minutes
            continue
        private_memory = proc.memory_info().private
        if (private_memory > MAX_MEMORY):
            print("Server has exceded the allowed maximum memory... restarting.")
            shutdown_server(proc, unique_id)
            errorcode = WERKZEUG_RESTART_CODE
        last_checked = time.time()


def kill_proc_tree(proc):
    for child in proc.children():
        kill_proc_tree(child)
    proc.kill()


def shutdown_server(proc, unique_id=None):
    import json
    import requests
    from app.config import PREBOORU_PORT, DATA_DIRECTORY
    from app.logical.file import put_get_raw
    if proc is None:
        return
    if unique_id is not None:
        try:
            resp = requests.post(f'http://127.0.0.1:{PREBOORU_PORT}/shutdown?uid={unique_id}', timeout=30)
            data = resp.json()
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"Connection error: {repr(e)}")
        except json.decoder.JSONDecodeError as e:
            print(f"Data error: {repr(e)}")
            put_get_raw(os.path.join(DATA_DIRECTORY, SHUTDOWN_ERROR_FILE), 'w', resp.text)
        else:
            if data['error']:
                print(f"Error with shutdown: {data['message']}",)
    print("Killing server...")
    kill_proc_tree(proc)


# #### Main functions

def main(args):
    switcher = {
        'server': start_server,
        'init': init_db,
        'watchdog': server_watchdog,
        'kill': kill_server,
    }
    switcher[args.type](args)


def check_other_execs():
    global PREBOORU_APP, DB, HAS_EXTERNAL_IMAGE_SERVER
    import sys
    exec_name = os.path.split(sys.argv[0])[-1]
    if exec_name == 'flask':
        from app import PREBOORU_APP, DB
        command = sys.argv[1]
        if command == 'db':
            initialize_migrate()
        elif command == 'routes':
            from app.config import HAS_EXTERNAL_IMAGE_SERVER
            initialize_controllers()


# ## EXECUTION START

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('type', choices=['init', 'server', 'watchdog', 'kill'])
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
    parser.add_argument('--unique-id', required=False, help="Unique identifier required to access admin routes.")
    args = parser.parse_args()
    main(args)
else:
    check_other_execs()
