# APP\__INIT__.PY

# ## PYTHON IMPORTS
import os
import sys
from io import BytesIO
from types import SimpleNamespace
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import event, MetaData, Table, Column, String, select
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.wsgi import get_input_stream
from werkzeug.formparser import parse_form_data

# ## LOCAL IMPORTS
from .logical import query_extensions
from .config import DB_PATH, JOBS_PATH, DEBUG_MODE

# #### Python Check

if sys.version_info.major == 3 and sys.version_info.minor < 7:
    print("Python version must be at least 3.7 to run this application.")
    exit(-1)


# ## GLOBAL VARIABLES

DATABASE_VERSION = 'e0f58422fc61'

# For imports outside the relative path
PREBOORU_DB_URL = os.environ.get('PREBOORU_DB', 'sqlite:///%s' % DB_PATH)
SCHEDULER_DB_URL = os.environ.get('SCHEDULER_JOBSTORES', r'sqlite:///%s' % JOBS_PATH)

NAMING_CONVENTION = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

SERVER_INFO = SimpleNamespace(addr="127.0.0.1")


# ## FUNCTIONS

def _fk_pragma_on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL2")
    cursor.close()


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
        print("Server addr:", SERVER_INFO.addr)
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

SCHEDULER_JOBSTORES = SQLAlchemyJobStore(url=SCHEDULER_DB_URL + "?check_same_thread=true", engine_options={'isolation_level': "AUTOCOMMIT"})

PREBOORU_APP = Flask("", template_folder=os.path.join('app', 'templates'), static_folder=os.path.join('app', 'static'))
PREBOORU_APP.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=PREBOORU_DB_URL,
    SQLALCHEMY_BINDS={},
    SQLALCHEMY_ENGINE_OPTIONS={'connect_args': {"check_same_thread": False}} if 'sqlite' in PREBOORU_DB_URL else {},
    JSON_SORT_KEYS=False,
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=DEBUG_MODE,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    EXPLAIN_TEMPLATE_LOADING=False,
    SCHEDULER_JOBSTORES={"default": SCHEDULER_JOBSTORES},
    SCHEDULER_EXECUTORS={"default": {"type": "processpool", "max_workers": 3}},
    SCHEDULER_JOB_DEFAULTS={"coalesce": False, "max_instances": 1, 'misfire_grace_time': 30},
    SCHEDULER_MISFIRE_GRACE_TIME=30,
    SCHEDULER_API_ENABLED=True,
)

SCHEDULER = APScheduler()
SCHEDULER.init_app(PREBOORU_APP)

METADATA = MetaData(naming_convention=NAMING_CONVENTION)
DB = SQLAlchemy(PREBOORU_APP, metadata=METADATA)
SESSION = DB.session

event.listen(DB.engine, 'connect', _fk_pragma_on_connect)
event.listen(SCHEDULER_JOBSTORES.engine, 'connect', _fk_pragma_on_connect)

PREBOORU_APP.wsgi_app = MethodRewriteMiddleware(PREBOORU_APP.wsgi_app)

# Scheduled tasks must be added only after everything else has been initialized
from .logical.tasks import schedule  # noqa: E402, F401


# #### Extend Python imports

query_extensions.Initialize()
