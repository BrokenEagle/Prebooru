<%!
    import re
%># MIGRATIONS/VERSIONS/${up_revision.upper()}_${"_".join(re.findall(r"\w+", message or "")).upper()}.PY
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}
# ## PACKAGE IMPORTS
# Add migrations or other local imports here


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()
<%
    from flask import current_app
    db_names = [''] + list(current_app.config.get("SQLALCHEMY_BINDS").keys())
%>
% for db_name in db_names:

def upgrade_${db_name}():
    ${context.get("%s_upgrades" % db_name, "pass")}


def downgrade_${db_name}():
    ${context.get("%s_downgrades" % db_name, "pass")}

% endfor
