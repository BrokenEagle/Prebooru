# FIXES/003_QUERY_AND_ADD_DANBOORU_ID_TO_POSTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global check_all_boorus
    sys.path.append(os.path.abspath('.'))
    from app.logical.check.boorus import check_all_boorus


def main():
    check_all_boorus()


# ## EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
