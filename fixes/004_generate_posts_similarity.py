# FIXES/004_GENERATE_POSTS_SIMILARITY.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
from sqlalchemy import func, not_


# ## FUNCTIONS

def initialize():
    global SESSION, Post, SimilarityData, generate_post_image_hashes
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Post, SimilarityData
    from app.logical.similarity.generate_data import generate_post_image_hashes


def standard_generate_posts_image_matches(args):
    if args.expunge:
        SimilarityData.query.delete()
        SESSION.commit()
        max_post_id = 0
    else:
        max_post_id = SESSION.query(func.max(SimilarityData.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).count_paginate(per_page=100)
    while True:
        print("\n%d/%d\n" % (page.page, page.total))
        for post in page.items:
            generate_post_image_hashes(post)
        if not page.has_next:
            break
        page = page.next()


def missing_generate_posts_image_matches(args):
    primaryjoin = Post.image_hashes.property.primaryjoin
    subquery = Post.query.join(primaryjoin.right.table, primaryjoin.left == primaryjoin.right)\
                   .filter(primaryjoin.left == primaryjoin.right).with_entities(Post.id)
    subclause = Post.id.in_(subquery)
    query = Post.query.filter(not_(subclause)).order_by(Post.id.asc())
    page = query.limit_paginate(per_page=100)
    while True:
        print("\n%d/%d\n" % (page.page, page.total))
        for post in page.items:
            generate_post_image_hashes(post)
        if not page.has_prev:
            break
        page = page.prev()


def main(args):
    if args.missing:
        missing_generate_posts_image_matches(args)
    else:
        standard_generate_posts_image_matches(args)


# ## EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to generate image match data for posts.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true",
                        help="Expunge all image match records.")
    parser.add_argument('--missing', required=False, default=False, action="store_true",
                        help="Generate image matches missing on posts.")
    args = parser.parse_args()

    initialize()
    main(args)
