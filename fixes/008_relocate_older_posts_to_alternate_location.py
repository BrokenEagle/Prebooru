# FIXES/008_RELOCATE_OLDER_POSTS_TO_ALTERNATE_LOCATION.PY

# ## PYTHON IMPORTS
import os
import sys


# ## FUNCTIONS

def initialize():
    global relocate_old_posts_to_alternate
    sys.path.append(os.path.abspath('.'))
    from app.logical.records.post_rec import relocate_old_posts_to_alternate


def main():
    relocate_old_posts_to_alternate()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
