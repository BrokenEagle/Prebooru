# FIXES/001_QUERY_AND_ADD_DANBOORU_ID_TO_POSTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global CheckAllArtistsForBoorus
    sys.path.append(os.path.abspath('.'))
    from app.logical.check_booru_artists import CheckAllArtistsForBoorus


def main():
    CheckAllArtistsForBoorus()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
