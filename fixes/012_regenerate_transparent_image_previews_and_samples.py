# FIXES/011_REGENERATE_TRANSPARENT_IMAGE_PREVIEWS_AND_SAMPLES.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
from PIL import Image


# ## FUNCTIONS

def initialize():
    global Post, check_alpha, convert_alpha, create_preview, create_sample
    sys.path.append(os.path.abspath('.'))
    from app.models import Post
    from app.logical.downloader.base import check_alpha, convert_alpha, create_preview, create_sample


def main(args):
    query = Post.query.filter(Post.file_ext == 'png')
    if args.startid:
        query = query.filter(Post.id >= args.startid)
    query = query.order_by(Post.id.asc())
    page = query.count_paginate(per_page=100)
    while True:
        print(f"regenerate_transparent_image_previews: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            image = Image.open(post.file_path)
            if check_alpha(image) and (post.has_sample or post.has_preview):
                print("Fixing alpha post:", post.shortlink)
                nonalpha_image = convert_alpha(image)
                if post.has_sample:
                    create_sample(nonalpha_image, post)
                if post.has_preview:
                    create_preview(nonalpha_image, post)
        if not page.has_next:
            break
        page = page.next()


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to regenerate transparent previews.")
    parser.add_argument('--startid', required=False, type=int,
                        help="ID of post to start at.")
    args = parser.parse_args()

    initialize()
    main(args)
