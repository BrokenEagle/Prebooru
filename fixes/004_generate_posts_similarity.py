# FIXES/004_GENERATE_POSTS_SIMILARITY.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
from sqlalchemy import func, not_


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityData, generate_post_similarity
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Post, SimilarityData
    from app.logical.similarity.generate_data import generate_post_similarity


def main(args):
    if args.missing:
        primaryjoin = Post.similarity_data.property.primaryjoin
        subquery = Post.query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right).filter(primaryjoin.left == primaryjoin.right).with_entities(Post.id)
        subclause = Post.id.in_(subquery)
        page = Post.query.filter(not_(subclause)).count_paginate(per_page=100)
    else:
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
    parser.add_argument('--missing', required=False, default=False, action="store_true", help="Generate similarity data missing on posts.")
    args = parser.parse_args()

    initialize()
    main(args)
