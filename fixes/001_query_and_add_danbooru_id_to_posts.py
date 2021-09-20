# FIXES/001_QUERY_AND_ADD_DANBOORU_ID_TO_POSTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global CheckAllPostsForDanbooruID
    sys.path.append(os.path.abspath('.'))
    from app.logical.check.posts import CheckAllPostsForDanbooruID


def main():
    CheckAllPostsForDanbooruID()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
