# FIXES/005_GENERATE_SIMILARITY_MATCHES.PY

# ## PYTHON IMPORTS
import os
import sys
import colorama
from argparse import ArgumentParser
from sqlalchemy.orm import selectinload


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityMatch, generate_similarity_matches, missing_similarity_matches_query,\
        print_info
    colorama.init(autoreset=True)
    sys.path.append(os.path.abspath('.'))
    from utility.uprint import print_info
    from app import SESSION
    from app.models import Post, SimilarityMatch
    from app.logical.database.post_db import missing_similarity_matches_query
    from app.logical.records.similarity_match_rec import generate_similarity_matches


def main(args):
    if args.expunge:
        SimilarityMatch.query.delete()
        Post.query.update({'simcheck': False})
        SESSION.commit()
    query = missing_similarity_matches_query()
    query = query.options(selectinload(Post.image_hashes))
    page = query.limit_paginate(per_page=50)
    while True:
        print_info(f"\ngenerate_similarity_matches: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            generate_similarity_matches(post)
        SESSION.commit()
        if not page.has_next:
            break
        page = page.next()


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to generate similarity matches.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true",
                        help="Expunge all similarity match records.")
    args = parser.parse_args()

    initialize()
    main(args)
