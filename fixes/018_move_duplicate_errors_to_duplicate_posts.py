# FIXES/018_MOVE_DUPLICATE_ERRORS_TO_DUPLICATE_POSTS.PY

# ## PYTHON IMPORTS
import os
import re
import sys
import itertools
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import attributes, selectinload


# ## GLOBAL VARIABLES

POSTID_RG = re.compile(r'post #(\d+)')


# ## FUNCTIONS

def initialize():
    global SESSION, Upload, SubscriptionElement, Error, search_attributes, get_posts_by_id
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Upload, SubscriptionElement, Error
    from app.logical.searchable import search_attributes
    from app.logical.database.post_db import get_posts_by_id


def create_duplicate_posts(model):
    q = model.query
    q = search_attributes(q, model, {'errors': {'message_ilike': '*already uploaded*'}})
    q = q.options(selectinload(model.errors), selectinload(model.duplicate_posts))
    page = q.count_paginate(per_page=200)
    while True:
        print(f"\ncreate_duplicate_posts: {page.first} - {page.last} / Total({page.count})\n")
        if len(page.items) == 0:
            break
        all_errors = list(itertools.chain(*[item.errors for item in page.items]))
        post_ids = set(map(int, itertools.chain(*(POSTID_RG.findall(error.message) for error in all_errors))))
        posts = get_posts_by_id(list(post_ids))
        duplicate_index = set()
        for item in page.items:
            for error in item.errors:
                match = POSTID_RG.search(error.message)
                if not match:
                    continue
                post_id = int(match.group(1))
                if any(duplicate for duplicate in item.duplicate_posts if duplicate.post_id == post_id):
                    continue
                post = next((post for post in posts if post.id == post_id), None)
                if post is None:
                    continue
                key = f"{post.id}-{item.id}"
                if key in duplicate_index:
                    continue
                post.duplicate_records.append(item)
                print('.', end="", flush=True)
                duplicate_index.add(key)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()
    print('\n')


def delete_duplicate_error_records():
    error_ids = [e[0] for e in Error.query.filter(Error.message.ilike('%already uploaded on post #%')).with_entities(Error.id)]
    for i in range(0, len(error_ids), 500):
        sublist = error_ids[i: i + 500]
        Error.query.filter(Error.id.in_(sublist)).delete()
        SESSION.commit()
        print('.', end="", flush=True)
    print('\n')


def main(args):
    if args.type in ['both', 'create']:
        for model in [Upload, SubscriptionElement]:
            print("Adding duplicate posts for:", model._model_name())
            create_duplicate_posts(model)
    if args.type in ['both', 'delete']:
        print("Deleting duplicate error records.")
        delete_duplicate_error_records()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to create duplicate post records from error records.")
    parser.add_argument('type', choices=['both', 'create', 'delete'],
                        help="Choose which step to perform.")
    args = parser.parse_args()

    initialize()
    main(args)
