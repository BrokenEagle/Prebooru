# FIXES/021_UPDATE_ARCHIVES_AFTER_REFACTOR.PY

# ## PYTHON IMPORTS
import os
import re
import sys
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import attributes


# ## FUNCTIONS

def initialize():
    global SESSION, Archive, SOURCES
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Archive
    from app.logical.sources import SOURCES


def fix_post_archives():
    query = Archive.query.enum_join(Archive.type_enum)
    query = query.filter(Archive.type_filter('name', '__eq__', 'post'))
    query = query.order_by(Archive.id.asc())
    page = query.count_paginate(per_page=100)
    while True:
        print(f"fix_post_archives: {page.first} - {page.last} / Total({page.count})")
        for arch in page.items:
            dirty = False
            if 'relations' in arch.data:
                arch.data['attachments'] = arch.data.pop('relations')
                dirty = True
            full_urls = []
            for url_data in arch.data['links']['illusts']:
                for source in SOURCES:
                    if isinstance(url_data, str):
                        continue
                    if source.is_partial_media_url(url_data['url']):
                        domain = source.get_domain_from_partial_url(url_data['url'])
                        url_data.pop('site', None)
                        url_data.pop('site_id', None)
                        url_data['domain'] = domain
                        full_urls.append("https://" + domain + url_data['url'])
                        break
            if len(full_urls) > 0:
                arch.data['links']['illusts'] = full_urls
                dirty = True
            if isinstance(arch.data['body']['type'], int):
                arch.data['body']['type'] = 'user'  # No way to tell at this point.
                dirty = True
            if dirty:
                attributes.flag_modified(arch, 'data')
                SESSION.flush()
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def main(args):
    if args.type == 'post':
        fix_post_archives()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to rewrite all archive fields to their current representation.")
    parser.add_argument('type', choices=['post'], help="Choose item to update.")
    args = parser.parse_args()

    initialize()
    main(args)
