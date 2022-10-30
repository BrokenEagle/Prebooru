# APP/__INIT__.PY

# ## PYTHON IMPORTS
import os
import re
import sys
import json
import uuid
import atexit
import logging
import traceback
from io import BytesIO
from types import SimpleNamespace

# ## EXTERNAL IMPORTS
from flask import Flask, request, jsonify
from sqlalchemy import event, MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from werkzeug.wsgi import get_input_stream
from werkzeug.formparser import parse_form_data
from werkzeug.exceptions import HTTPException

# ## PACKAGE IMPORTS
from config import DB_PATH, JOBS_PATH, DEBUG_MODE, NAMING_CONVENTION, DEBUG_LOG, LOGHANDLER
from utility import RepeatTimer, is_interactive_shell
from utility.uprint import buffered_print

# ## LOCAL IMPORTS
from .logical import query_extensions
from .logical.validate import validate_python


# ## GLOBAL VARIABLES

# For imports outside the relative path
PREBOORU_DB_URL = os.environ.get('PREBOORU_DB', 'sqlite:///%s' % DB_PATH)
SCHEDULER_DB_URL = os.environ.get('SCHEDULER_JOBSTORES', r'sqlite:///%s' % JOBS_PATH)

ENGINE_OPTIONS = {
    'json_serializer': lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':')),
    'connect_args': {
        'check_same_thread': False,
        'timeout': 60},
    'echo_pool': True,
    'pool_recycle': 15,
}

SERVER_INFO = SimpleNamespace(addr="127.0.0.1", allow_requests=True, active_requests=0, unique_id=None)
DATABASE_INFO = SimpleNamespace(connections={'prebooru': set(), 'jobs': set()})

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG_LOG else logging.WARNING)
logger.addHandler(LOGHANDLER)


# ## FUNCTIONS

def _fk_pragma_on_connect(dbapi_connection, connection_record, database):
    if DEBUG_LOG:
        dbapi_connection.set_trace_callback(print)
    connection_record.uuid = str(uuid.uuid4())
    connection_record.pid = os.getpid()
    DATABASE_INFO.connections[database].add(connection_record.uuid)
    logger.debug('DBOPEN-%s(%d) [%d]--%s--', database, len(DATABASE_INFO.connections[database]),
                 connection_record.pid, connection_record.uuid)
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()
    if mode != ('wal',):
        cursor.execute("PRAGMA journal_mode = wal;")
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()
        if mode != ('wal',):
            logger.error("Unable to set journal mode to WAL")
    cursor.execute('PRAGMA synchronous = NORMAL')
    cursor.execute('PRAGMA temp_store = MEMORY')
    cursor.execute('PRAGMA mmap_size = 0x7FFF0000')
    cursor.execute('PRAGMA cache_size = -32000')
    cursor.close()


def _fk_pragma_on_close(dbapi_connection, connection_record, database):
    DATABASE_INFO.connections[database].discard(connection_record.uuid)
    logger.debug('DBCLOSE-%s(%d) [%d]--%s--', database, len(DATABASE_INFO.connections[database]),
                 connection_record.pid, connection_record.uuid)
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA analysis_limit = 400')
    cursor.execute('PRAGMA optimize')
    cursor.close()


def _fk_open_connections():
    printer = buffered_print("OPEN DB CONNECTIONS")
    printer("PID:", os.getpid())
    for key in DATABASE_INFO.connections:
        printer('  %s: %d' % (key, len(DATABASE_INFO.connections[key])))
        for uid in DATABASE_INFO.connections[key]:
            printer('    %s' % uid)
    printer.print()


def _before_request():
    from app.logical.database.server_info_db import update_last_activity
    logger.info("Before request: Allow - %s, Active = %d\n", SERVER_INFO.allow_requests, SERVER_INFO.active_requests)
    SERVER_INFO.active_requests += 1
    if request.endpoint is not None and not re.match(r'^(?:shutdown|ping|scheduler|static|media)', request.endpoint):
        try:
            update_last_activity('user')
        except Exception as e:
            # Don't fail the request if the database is locked
            logger.warning(f"Unable to update last activity:\r\n {e}")
    return None if SERVER_INFO.allow_requests else ""


def _teardown_request(error=None):
    if error is not None:
        logger.warning(f"\nRequest error: {error}\n")
    logger.info("After request: Allow - %s, Active = %d\n", SERVER_INFO.allow_requests, SERVER_INFO.active_requests)
    SERVER_INFO.active_requests = max(SERVER_INFO.active_requests - 1, 0)


def _error_handler(error):
    SESSION.remove()
    if not request.path.endswith('.json'):
        if issubclass(error.__class__, HTTPException):
            return error.get_response()
        else:
            # Reraising and having the Werkzeug catch the exception prevents the _teardown request from running
            SERVER_INFO.active_requests = max(SERVER_INFO.active_requests - 1, 0)
            raise error
    exc_type, exc_value, exc_tb = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_tb)
    fmt_tb = traceback.format_exception(exc_type, exc_value, exc_tb)
    resp = jsonify({
        'error': True,
        'message': repr(error),
        'traceback': fmt_tb,
        'endpoint': request.endpoint,
        'args': {k: v for (k, v) in request.args.items()},
        'data': {k: v for (k, v) in request.form.items()},
        'files': {k: f"{v.filename} ({v.mimetype})" for (k, v) in request.files.items()},
    })
    if issubclass(error.__class__, HTTPException):
        resp.status_code = error.code
    else:
        resp.status_code = 520
    return resp


@atexit.register
def _close_session():
    SESSION.close()


# ## CLASSES

class MethodRewriteMiddleware(object):
    allowed_methods = frozenset([
        'GET',
        'HEAD',
        'POST',
        'DELETE',
        'PUT',
        'PATCH',
        'OPTIONS'
    ])
    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

    def __init__(self, app, input_name='_method'):
        self.app = app
        self.input_name = input_name

    def __call__(self, environ, start_response):
        SERVER_INFO.addr = environ['HTTP_HOST'].split(':')[0]
        logger.info("Middleware: Server addr - %d\n", SERVER_INFO.addr)
        if environ['REQUEST_METHOD'] == 'POST':
            environ['wsgi.input'] = stream = BytesIO(get_input_stream(environ).read())
            _, form, _ = parse_form_data(environ)
            form_method = form.get(self.input_name, default='').upper()
            if form_method in self.allowed_methods:
                environ['REQUEST_METHOD'] = form_method
            if form_method in self.bodyless_methods:
                environ['CONTENT_LENGTH'] = '0'
            stream.seek(0)
        return self.app(environ, start_response)


# ## INITIALIZATION

# Validate Python before executing any application code
validate_python()

SCHEDULER_JOBSTORES = SQLAlchemyJobStore(url=SCHEDULER_DB_URL + '?check_same_thread=true',
                                         engine_options={'isolation_level': 'AUTOCOMMIT'})

PREBOORU_APP = Flask("", template_folder=os.path.join('app', 'templates'), static_folder=os.path.join('app', 'static'))
PREBOORU_APP.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=PREBOORU_DB_URL,
    SQLALCHEMY_BINDS={
        'jobs': SCHEDULER_DB_URL,
    },
    SQLALCHEMY_ENGINE_OPTIONS=ENGINE_OPTIONS,
    JSON_SORT_KEYS=False,
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=DEBUG_MODE,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    EXPLAIN_TEMPLATE_LOADING=False,
    SEND_FILE_MAX_AGE_DEFAULT=43200,
    SCHEDULER_JOBSTORES={'default': SCHEDULER_JOBSTORES},
    SCHEDULER_EXECUTORS={'default': {'type': 'processpool', 'max_workers': 3}},
    SCHEDULER_JOB_DEFAULTS={'coalesce': False, 'max_instances': 1, 'misfire_grace_time': 30},
    SCHEDULER_MISFIRE_GRACE_TIME=30,
    SCHEDULER_API_ENABLED=True,
)

SCHEDULER = APScheduler()
SCHEDULER.init_app(PREBOORU_APP)

METADATA = MetaData(naming_convention=NAMING_CONVENTION)
DB = SQLAlchemy(PREBOORU_APP, metadata=METADATA)
SESSION = DB.session

event.listen(DB.get_engine(bind=None).engine, 'connect', lambda conn, rec: _fk_pragma_on_connect(conn, rec, 'prebooru'))
event.listen(DB.get_engine(bind='jobs').engine, 'connect', lambda conn, rec: _fk_pragma_on_connect(conn, rec, 'jobs'))
event.listen(DB.get_engine(bind=None).engine, 'close', lambda conn, rec: _fk_pragma_on_close(conn, rec, 'prebooru'))
event.listen(DB.get_engine(bind='jobs').engine, 'close', lambda conn, rec: _fk_pragma_on_close(conn, rec, 'jobs'))

PREBOORU_APP.wsgi_app = MethodRewriteMiddleware(PREBOORU_APP.wsgi_app)
PREBOORU_APP.before_request(_before_request)
PREBOORU_APP.teardown_request(_teardown_request)
PREBOORU_APP.errorhandler(Exception)(_error_handler)

if DEBUG_LOG and not is_interactive_shell() and (not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
    RECHECK_DB = RepeatTimer(60, _fk_open_connections, jitter=True)
    RECHECK_DB.setDaemon(True)
    RECHECK_DB.start()

# #### Extend Python imports
query_extensions.initialize()
