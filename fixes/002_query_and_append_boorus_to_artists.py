# FIXES/002_QUERY_AND_APPEND_BOORUS_TO_ARTISTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global CheckAllArtistsForBoorus
    sys.path.append(os.path.abspath('.'))
    from app.logical.check.booru_artists import CheckAllArtistsForBoorus


def main():
    CheckAllArtistsForBoorus()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
