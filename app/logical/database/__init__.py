# APP/LOGICAL/DATABASE/__INIT__.PY

"""For logic on DB operations with models, such as creating, updating, deleting, querying, and committing."""

from utility import is_interactive_shell

if is_interactive_shell():
    from .server_info_db import initialize_server_fields
    initialize_server_fields()
