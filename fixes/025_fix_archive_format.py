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
    global SESSION, Archive, print_info, safe_get, swap_key_value
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Archive
    from app.models.base import json_column
    from utility.uprint import print_info
    from utility.data import safe_get, swap_key_value
    Archive.data = json_column(nullable=False)


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


def fix_illust_archives():
    query = Archive.query
    query = query.filter(Archive.type_value == 'illust')
    query = query.order_by(Archive.id.asc())
    page = query.count_paginate(per_page=100)
    body_keys = ['site', 'site_illust_id', 'site_created', 'title', 'commentary', 'pages', 'score',
                 'active', 'updated', 'created']
    nonnull_keys = ['site', 'site_illust_id', 'pages', 'score', 'active', 'updated', 'created']
    while True:
        print_info(f"fix_illust_archives: {page.first} - {page.last} / Total({page.count})")
        for arch in page.items:
            original_body_params = arch.data['body']
            updated_body_params = {k: v for (k, v) in original_body_params.items() if k in body_keys}
            for k in body_keys:
                updated_body_params.setdefault(k, None)
            arch.data['scalars'].setdefault('titles', [])
            arch.data['scalars'].setdefault('commentaries', [])
            arch.data['scalars'].setdefault('additional_commentaries', [])
            if updated_body_params['title'] is None:
                updated_body_params['title'] = safe_get(arch.data['attachments'], 'data', 'title')
            if updated_body_params['commentary'] is None and len(arch.data['scalars']['commentaries']) > 0:
                updated_body_params['commentary'] = arch.data['scalars']['commentaries'][0]
                arch.data['scalars']['commentaries'] = arch.data['scalars']['commentaries'][1:]
            bad_columns = [k for k in updated_body_params.keys()
                           if k in nonnull_keys and updated_body_params.get(k) is None]
            if len(bad_columns):
                # Leaving this to the user to fix
                print(arch.shortlink, "Null values for nonnull columns found:", bad_columns)
                input()
                print("Skipping...")
                continue
            arch.data['body'] = updated_body_params
            attributes.flag_modified(arch, 'data')
            SESSION.flush()
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def fix_artist_archives():
    query = Archive.query
    query = query.filter(Archive.type_value == 'artist')
    query = query.order_by(Archive.id.asc())
    page = query.count_paginate(per_page=100)
    body_keys = ['site', 'site_artist_id', 'site_created', 'site_account', 'name',
                 'profile', 'active', 'primary', 'updated', 'created']
    nonnull_keys = ['site', 'site_artist_id', 'site_account', 'active', 'primary', 'updated', 'created']
    while True:
        print_info(f"fix_artist_archives: {page.first} - {page.last} / Total({page.count})")
        for arch in page.items:
            original_body_params = arch.data['body']
            updated_body_params = {k: v for (k, v) in original_body_params.items() if k in body_keys}
            for k in body_keys:
                updated_body_params.setdefault(k, None)
            swap_key_value(arch.data['scalars'], 'accounts', 'site_accounts')
            arch.data['scalars'].setdefault('site_accounts', [])
            arch.data['scalars'].setdefault('names', [])
            arch.data['scalars'].setdefault('profiles', [])
            if updated_body_params['site_account'] is None and len(arch.data['scalars']['site_accounts']) > 0:
                updated_body_params['site_account'] = arch.data['scalars']['site_accounts'][0]
                arch.data['scalars']['site_accounts'] = arch.data['scalars']['site_accounts'][1:]
            if updated_body_params['name'] is None and len(arch.data['scalars']['names']) > 0:
                updated_body_params['name'] = arch.data['scalars']['names'][0]
                arch.data['scalars']['names'] = arch.data['scalars']['names'][1:]
            if updated_body_params['profile'] is None and len(arch.data['scalars']['profiles']) > 0:
                updated_body_params['profile'] = arch.data['scalars']['profiles'][0]
                arch.data['scalars']['profiles'] = arch.data['scalars']['profiles'][1:]
            bad_columns = [k for k in updated_body_params.keys()
                           if k in nonnull_keys and updated_body_params.get(k) is None]
            if len(bad_columns):
                # Leaving this to the user to fix
                print(arch.shortlink, "Null values for nonnull columns found:", bad_columns)
                input()
                print("Skipping...")
                continue
            arch.data['body'] = updated_body_params
            attributes.flag_modified(arch, 'data')
            SESSION.flush()
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def fix_booru_archives():
    query = Archive.query
    query = query.filter(Archive.type_value == 'booru')
    query = query.order_by(Archive.id.asc())
    page = query.count_paginate(per_page=100)
    body_keys = ['danbooru_id', 'name', 'banned', 'deleted', 'updated', 'created']
    nonnull_keys = ['name', 'banned', 'deleted', 'updated', 'created']
    while True:
        print_info(f"fix_booru_archives: {page.first} - {page.last} / Total({page.count})")
        for arch in page.items:
            original_body_params = arch.data['body']
            updated_body_params = {k: v for (k, v) in original_body_params.items() if k in body_keys}
            for k in body_keys:
                updated_body_params.setdefault(k, None)
            swap_key_value(updated_body_params, 'current_name', 'name')
            arch.data['scalars'].setdefault('names', [])
            arch.data['scalars'].setdefault('profiles', [])
            if updated_body_params['name'] is None and len(arch.data['scalars']['names']) > 0:
                updated_body_params['name'] = arch.data['scalars']['names'][0]
                arch.data['scalars']['names'] = arch.data['scalars']['names'][1:]
            bad_columns = [k for k in updated_body_params.keys()
                           if k in nonnull_keys and updated_body_params.get(k) is None]
            if len(bad_columns):
                # Leaving this to the user to fix
                print(arch.shortlink, "Null values for nonnull columns found:", bad_columns)
                input()
                print("Skipping...")
                continue
            arch.data['body'] = updated_body_params
            attributes.flag_modified(arch, 'data')
            SESSION.flush()
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
    elif args.type == 'illust':
        fix_illust_archives()
    elif args.type == 'artist':
        fix_artist_archives()
    elif args.type == 'booru':
        fix_booru_archives()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to ensure unneeded values are"
                                        "removed and nonnull values are present.")
    parser.add_argument('type', choices=['post', 'illust', 'artist', 'booru'], help="Choose item to update.")
    args = parser.parse_args()

    initialize()
    main(args)
