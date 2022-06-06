# FIXES/007_QUERY_AND_REDOWNLOAD_POSTS_WITH_MISMATCHING_MD5S.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global check_posts_for_valid_md5
    sys.path.append(os.path.abspath('.'))
    from app.logical.check.posts import check_posts_for_valid_md5


def main():
    check_posts_for_valid_md5()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
