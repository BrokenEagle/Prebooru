# FIXES/002_QUERY_AND_APPEND_BOORUS_TO_ARTISTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global check_all_artists_for_boorus
    sys.path.append(os.path.abspath('.'))
    from app.logical.check.booru_artists import check_all_artists_for_boorus


def main():
    check_all_artists_for_boorus()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
