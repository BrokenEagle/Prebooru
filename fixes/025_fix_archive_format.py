# FIXES/025_FIX_ARCHIVE_FORMAT.PY

# ## PYTHON IMPORTS
import os
import sys
import colorama
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import attributes


# ## FUNCTIONS

def initialize():
    global SESSION, Archive, print_info
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Archive, Post
    from utility.uprint import print_info


def fix_post_archives():
    query = Archive.query
    query = query.filter(Archive.type_value == 'post')
    query = query.order_by(Archive.id.asc())
    page = query.count_paginate(per_page=100)
    body_keys = ['size', 'pixel_md5', 'type', 'duration', 'width', 'md5',
                 'file_ext', 'audio', 'created', 'danbooru_id', 'height']
    nonnull_keys = ['size', 'type', 'width', 'md5', 'file_ext', 'created', 'height']
    while True:
        print_info(f"fix_post_archives: {page.first} - {page.last} / Total({page.count})")
        dirty = False
        for arch in page.items:
            original_body_params = arch.data['body']
            updated_body_params = {k: v for (k, v) in original_body_params.items() if k in body_keys}
            for k in body_keys:
                updated_body_params.setdefault(k, None)
            bad_columns = [k for k in updated_body_params.keys()
                           if k in nonnull_keys and updated_body_params.get(k) is None]
            if len(bad_columns):
                # Leaving this to the user to fix
                print(arch.shortlink, "Null values for nonnull columns found:", bad_columns)
                input()
                print("Skipping...")
                continue
            if original_body_params != updated_body_params:
                print(arch.shortlink, "Will update body params.")
                arch.data['body'] = updated_body_params
                attributes.flag_modified(arch, 'data')
                dirty = True
                SESSION.flush()
        if dirty:
            SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def main(args):
    """
    Fixes the body format of archive records. The attachments, scalaras, and links will just be converted to text,
    so the format isn't as necessary to check on at this time.
    """
    colorama.init(autoreset=True)
    if args.type == 'post':
        fix_post_archives()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to ensure unneeded values are"
                                        "removed and nonnull values are present.")
    parser.add_argument('type', choices=['post'], help="Choose item to update.")
    args = parser.parse_args()

    initialize()
    main(args)
