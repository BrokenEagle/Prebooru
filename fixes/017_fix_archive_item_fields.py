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
ARCHIVEKEY_RG = re.compile(r'(\d+)-(\d+)')

# ## FUNCTIONS

def initialize():
    global SESSION, Archive, post_type, site_descriptor, get_directory_listing, put_get_json
    sys.path.append(os.path.abspath('.'))
    from utility.file import get_directory_listing, put_get_json
    from app import SESSION
    from app.models import Archive
    from app.enum_imports import post_type, site_descriptor


def get_migrations():
    migration_directory = os.path.join(os.getcwd(), 'migrations', 'enum_versions', 'default')
    migration_files = get_directory_listing(migration_directory)
    migrations = [put_get_json(os.path.join(migration_directory, file), 'r') for file in migration_files]
    ordered_migrations = []
    rev = None
    for _ in range(len(migrations)):
        next_migration = next((migration for migration in migrations if migration['down'] == rev))
        ordered_migrations.append(next_migration)
        rev = next_migration['rev']
    return ordered_migrations


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


def update_archive_enums():
    migrations = get_migrations()
    first_revision = migrations[0]
    post_mapping = {t['id']: t['name'] for t in first_revision['tables']['post_type']}
    site_descriptor_mapping = {t['id']: t['name'] for t in first_revision['tables']['site_descriptor']}
    page = Archive.query.filter(Archive.type_filter('name', 'in_', ['post', 'illust', 'artist']))\
                        .count_paginate(per_page=100)
    while True:
        print(f"update_archives: {page.first} - {page.last} / Total({page.count})")
        for item in page.items:
            if item.type.name == 'post':
                if 'type_id' in item.data['body']:
                    old_type = item.data['body']['type_id']
                    del item.data['body']['type_id']
                else:
                    old_type = item.data['body']['type']
                item.data['body']['type'] = post_mapping[old_type] if isinstance(old_type, int) else old_type
            else:
                if 'site_id' in item.data['body']:
                    del item.data['body']['site_id']
                elif 'site' in item.data['body']:
                    del item.data['body']['site']
                match = ARCHIVEKEY_RG.match(item.key)
                if match:
                    site_id, site_item_id = match.groups()
                    site_name = site_descriptor_mapping[int(site_id)]
                    new_key = "%s-%s" % (site_name, site_item_id)
                    item.key = new_key
            if item.type.name == 'illust':
                if 'site_data' in item.data['relations'] and item.data['relations']['site_data'] is not None:
                    if 'type_id' in item.data['relations']['site_data']:
                        del item.data['relations']['site_data']['type_id']
                    else:
                        del item.data['relations']['site_data']['type']
                for illust_url in item.data['relations']['illust_urls']:
                    site_id = None
                    if 'site_id' in illust_url:
                        site_id = illust_url['site_id']
                        del illust_url['site_id']
                    elif 'site' in illust_url:
                        site_id = illust_url['site']
                        del illust_url['site']
                    sample_site_id = None
                    if 'sample_site_id' in illust_url:
                        sample_site_id = illust_url['sample_site_id']
                        del illust_url['sample_site_id']
                    elif 'sample_site' in illust_url:
                        sample_site_id = illust_url['sample_site']
                        del illust_url['sample_site']
                    if isinstance(site_id, int):
                        site_name = site_descriptor_mapping[site_id]
                        site = site_descriptor.by_name(site_name)
                        illust_url['url'] = 'https://' + site.domain + illust_url['url']
                    if isinstance(sample_site_id, int):
                        sample_site_name = site_descriptor_mapping[sample_site_id]
                        sample_site = sample_site_descriptor.by_name(sample_site_name)
                        illust_url['sample'] = 'https://' + sample_site.domain + illust_url['sample']
                for post in item.data['links']['posts']:
                    site_id = None
                    if 'site_id' in post:
                        site_id = post['site_id']
                        del post['site_id']
                    elif 'site' in post:
                        site_id = post['site']
                        del post['site']
                    if isinstance(site_id, int):
                        site_name = site_descriptor_mapping[site_id]
                        site = site_descriptor.by_name(site_name)
                        post['url'] = 'https://' + site.domain + post['url']
            attributes.flag_modified(item, "data")
            SESSION.flush()
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def main(args):
    if args.type == 'post':
        update_post_archives()
    elif args.type == 'enum':
        update_archive_enums()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to rewrite all archive fields to their current representation.")
    parser.add_argument('type', choices=['post', 'enum'], help="Choose item to update.")
    args = parser.parse_args()

    initialize()
    main(args)
