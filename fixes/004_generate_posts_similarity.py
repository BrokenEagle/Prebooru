# FIXES/004_GENERATE_POSTS_SIMILARITY.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
from sqlalchemy import func


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityData, generate_post_similarity
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models.post import Post
    from app.similarity import SimilarityData
    from app.logical.similarity.generate_data import generate_post_similarity


def main(args):
    if args.expunge:
        SimilarityData.query.delete()
        SESSION.commit()
        max_post_id = 0
    else:
        max_post_id = SESSION.query(func.max(SimilarityData.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).count_paginate(per_page=100)
    while True:
        print("\n%d/%d\n" % (page.page, page.pages))
        for post in page.items:
            generate_post_similarity(post)
        if not page.has_next:
            break
        page = page.next()


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to generate similarity data.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true", help="Expunge all similarity data records.")
    args = parser.parse_args()

    initialize()
    main(args)
