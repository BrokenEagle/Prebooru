# FIXES/017_FIX_ARCHIVE_ITEM_FIELDS.PY

# ## PYTHON IMPORTS
import os
import re
import sys
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import attributes


# ## GLOBAL VARIABLES

POSTTYPE_RG = re.compile(r'(user|subscription)_post')


# ## FUNCTIONS

def initialize():
    global SESSION, Archive, PostType
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Archive
    from app.models.post import PostType


def update_post_archives():
    page = Archive.query.filter_by(type='post').count_paginate(per_page=100)
    while True:
        print(f"update_post_archives: {page.first} - {page.last} / Total({page.count})")
        dirty = False
        for item in page.items:
            item_type = item.data['body']['type']
            if isinstance(item_type, str):
                match = POSTTYPE_RG.match(item_type)
                if match:
                    type_name = match.group(1)
                    item.data['body']['type'] = PostType[type_name].value
                    attributes.flag_modified(item, "data")
                    print("Updating", item.shortlink)
                    dirty = True
        if dirty:
            print("Committing")
            SESSION.commit()
        if not page.has_next:
            return
        page = page.next()


def main(args):
    if args.type == 'post':
        update_post_archives()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to rewrite all archive fields to their current representation.")
    parser.add_argument('type', choices=['post'], help="Choose item to update.")
    args = parser.parse_args()

    initialize()
    main(args)
