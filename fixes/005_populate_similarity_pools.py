# FIXES/005_POPULATE_SIMILARITY_POOLS.PY

# ## PYTHON IMPORTS
import os
import sys
import colorama
from argparse import ArgumentParser
from sqlalchemy import func, not_, or_
from sqlalchemy.orm import selectinload


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityMatch, SubscriptionElement, populate_similarity_pools, search_attributes,\
        TYPE_CLAUSE, SUBELEMENT_SUBQUERY,\
        print_info
    colorama.init(autoreset=True)
    sys.path.append(os.path.abspath('.'))
    from utility.uprint import print_info
    from app import SESSION
    from app.models import Post, SimilarityMatch, SubscriptionElement
    from app.logical.records.similarity_match_rec import populate_similarity_pools
    from app.logical.searchable import search_attributes
    TYPE_CLAUSE = Post.type_filter('name', '__eq__', 'user')
    SUBELEMENT_SUBQUERY = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                                   .with_entities(SubscriptionElement.post_id)


def expunge_populate_similarity_pools(args):
    SimilarityMatch.query.delete()
    SESSION.commit()
    page = Post.query.count_paginate(per_page=100)
    while True:
        print(f"\nexpunge_populate_similarity_pools: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            populate_similarity_pools(post)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def missing_populate_similarity_pools(args):
    query = Post.query.enum_join(Post.type_enum)
    query = query.filter(Post.simcheck.is_(False), or_(TYPE_CLAUSE, Post.id.not_in(SUBELEMENT_SUBQUERY)))
    query = query.options(selectinload(Post.image_hashes),
                          selectinload(Post.similarity_matches_forward),
                          selectinload(Post.similarity_matches_reverse))
    page = query.limit_paginate(per_page=100)
    while True:
        print_info(f"\nmissing_populate_similarity_pools: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            populate_similarity_pools(post)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


def main(args):
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
