# FIXES/003_QUERY_AND_UPDATE_BOORUS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global check_all_boorus
    sys.path.append(os.path.abspath('.'))
    from app.logical.records.booru_rec import check_all_boorus


def main():
    check_all_boorus()


# ## EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
