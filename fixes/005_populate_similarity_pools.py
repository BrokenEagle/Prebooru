# FIXES/005_POPULATE_SIMILARITY_POOLS.PY

# ## PYTHON IMPORTS
import os
import sys
import colorama
from argparse import ArgumentParser
from sqlalchemy.orm import selectinload


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityMatch, populate_similarity_pools, missing_similarity_matches_query,\
        print_info
    colorama.init(autoreset=True)
    sys.path.append(os.path.abspath('.'))
    from utility.uprint import print_info
    from app import SESSION
    from app.models import Post, SimilarityMatch
    from app.logical.database.post_db import missing_similarity_matches_query
    from app.logical.records.similarity_match_rec import populate_similarity_pools


def expunge_populate_similarity_pools():
    SimilarityMatch.query.delete()
    SESSION.commit()
    page = Post.query.count_paginate(per_page=50)
    while True:
        print(f"\nexpunge_populate_similarity_pools: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            populate_similarity_pools(post)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def missing_populate_similarity_pools():
    query = missing_similarity_matches_query()
    query = query.options(selectinload(Post.image_hashes))
    page = query.limit_paginate(per_page=50)
    while True:
        print_info(f"\nmissing_populate_similarity_pools: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            populate_similarity_pools(post)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def main():
    if args.missing:
        missing_populate_similarity_pools(args)
    elif args.expunge:
        expunge_populate_similarity_pools(args)


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to populate similarity pools.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true",
                        help="Expunge all similarity pool records.")
    parser.add_argument('--missing', required=False, default=False, action="store_true",
                        help="Generate similarity pools missing on posts.")
    args = parser.parse_args()

    initialize()
    main(args)
