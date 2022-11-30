# FIXES/018_MOVE_DUPLICATE_ERRORS_TO_DUPLICATE_POSTS.PY

# ## PYTHON IMPORTS
import os
import re
import sys
import itertools
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload


# ## GLOBAL VARIABLES

POSTID_RG = re.compile(r'post #(\d+)')


# ## FUNCTIONS

def initialize():
    global SESSION, Upload, IllustUrl, Error, UploadErrors, SubscriptionElementErrors,\
        selectinload_batch_primary, selectinload_batch_relations, populate_all_upload_elements
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Upload, IllustUrl, Error, UploadErrors, SubscriptionElementErrors
    from app.logical.batch_loader import selectinload_batch_relations
    from app.logical.records.upload_rec import populate_all_upload_elements


def create_missing_upload_elements():
    q = Upload.query
    q = q.options(selectinload(Upload.image_urls),
                  selectinload(Upload.elements),
                  selectinload(Upload.illust_url).selectinload(IllustUrl.illust),
                  selectinload(Upload.errors))
    page = q.count_paginate(per_page=200)
    while True:
        print(f"\npopulate_all_upload_elements: {page.first} - {page.last} / Total({page.count})\n")
        if len(page.items) == 0:
            break
        upload_elements = populate_all_upload_elements(page.items)
        all_elements = list(itertools.chain(*(upload_elements[k] for k in upload_elements)))
        selectinload_batch_relations(all_elements, 'illust_url', 'post')
        for upload in page.items:
            if upload.id not in upload_elements:
                print(f"\nSkipping {upload.shortlink} - {upload.status.name}")
                continue
            print(f"\nProcessing {upload.shortlink} - {upload.status.name}")
            elements = upload_elements[upload.id]
            for element in elements:
                if element.illust_url.post is None:
                    element.status = 'unknown'
                else:
                    element.md5 = element.illust_url.post.md5
                    iterator = itertools.chain(*(POSTID_RG.findall(error.message) for error in upload.errors))
                    error_post_ids = set(map(int, iterator))
                    if element.illust_url.post.id in error_post_ids:
                        element.status = 'error'
                    else:
                        element.status = 'complete'
                print(f"[{element.shortlink}] - {element.status}")
            SESSION.flush()
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()
    print('\n')


def delete_duplicate_error_records():
    error_ids = [e[0] for e in Error.query.filter(Error.message.ilike('%already uploaded on post #%'))
                                          .with_entities(Error.id)]
    for i in range(0, len(error_ids), 100):
        sublist = error_ids[i: i + 100]
        UploadErrors.query.filter(UploadErrors.error_id.in_(sublist)).delete()
        SubscriptionElementErrors.query.filter(SubscriptionElementErrors.error_id.in_(sublist)).delete()
        Error.query.filter(Error.id.in_(sublist)).delete()
        SESSION.flush()
        print('.', end="", flush=True)
    SESSION.commit()
    print('\n')


def main(args):
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.INFO)
    if args.type in ['both', 'create']:
        print("Creating upload elements.")
        create_missing_upload_elements()
    if args.type in ['both', 'delete']:
        print("Deleting duplicate error records.")
        delete_duplicate_error_records()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to create duplicate post records from error records.")
    parser.add_argument('type', choices=['both', 'create', 'delete'],
                        help="Choose which step to perform.")
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Log SQL commands.")
    args = parser.parse_args()

    initialize()
    main(args)
