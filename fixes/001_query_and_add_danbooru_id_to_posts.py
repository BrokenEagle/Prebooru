# FIXES/001_QUERY_AND_ADD_DANBOORU_ID_TO_POSTS.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global check_all_posts_for_danbooru_id
    sys.path.append(os.path.abspath('.'))
    from app.logical.records.post_rec import check_all_posts_for_danbooru_id


def main():
    check_all_posts_for_danbooru_id()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
