# FIXES/005_POPULATE_SIMILARITY_POOLS.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
from sqlalchemy import func


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityPool, SimilarityPoolElement, populate_similarity_pools
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models.post import Post
    from app.similarity import SimilarityPool, SimilarityPoolElement
    from app.logical.similarity.populate_pools import populate_similarity_pools


def main(args):
    if args.expunge:
        SimilarityPoolElement.query.update({SimilarityPoolElement.sibling_id: None}, synchronize_session=False)  # Sibling relationship must be removed first
        SESSION.commit()
        SimilarityPoolElement.query.delete()
        SESSION.commit()
        SimilarityPool.query.delete()
        SESSION.commit()
        max_post_id = 0
    else:
        max_post_id = SESSION.query(func.max(SimilarityPool.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).count_paginate(per_page=100)
    while True:
        print("\n%d/%d\n" % (page.page, page.pages))
        for post in page.items:
            populate_similarity_pools(post)
        if not page.has_next:
            break
        page = page.next()


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to populate similarity pools.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true", help="Expunge all similarity pool records.")
    args = parser.parse_args()

    initialize()
    main(args)
