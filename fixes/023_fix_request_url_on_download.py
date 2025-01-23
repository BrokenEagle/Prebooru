# FIXES/022_SET_STATUS_ON_DUPLICATE_ERROR_SUBSCRIPTION_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys

# ## EXTERNAL IMPORTS
from sqlalchemy import text


# ## GLOBAL VARIABLES

CREATE_TABLE = """
CREATE TABLE download_temp (
	id INTEGER NOT NULL, 
	request_url TEXT NOT NULL, 
	status_id INTEGER NOT NULL, 
	created INTEGER NOT NULL, 
	CONSTRAINT pk_download PRIMARY KEY (id), 
	CONSTRAINT fk_download_status_id_download_status FOREIGN KEY(status_id) REFERENCES download_status (id)
)
"""

INSERT_TABLE = """
INSERT INTO download_temp(id, request_url, status_id, created)
SELECT download.id, download.request_url, download.status_id, download.created
FROM download
"""


# ## FUNCTIONS

# #### Auxiliary functions

def initialize():
    global SESSION
    os.environ['USE_ENUMS'] = 'false'
    sys.path.append(os.path.abspath('.'))
    from app import SESSION


# #### Main execution functions

def main():
    initialize()
    SESSION.execute(text(CREATE_TABLE))
    SESSION.execute(text(INSERT_TABLE))
    SESSION.commit()
    SESSION.execute(text("PRAGMA foreign_keys = 0"))
    SESSION.execute(text("DROP TABLE download"))
    SESSION.execute(text("ALTER TABLE download_temp RENAME TO download"))
    SESSION.execute(text("PRAGMA foreign_keys = 1"))
    SESSION.commit()


# ##EXECUTION START

if __name__ == '__main__':
    main()
