# FIXES/013_CREATE_ANIMATED_MP4_SAMPLES_AND_PREVIEWS.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser


# ## FUNCTIONS

def initialize():
    global Post, convert_mp4_to_webp, convert_mp4_to_webm
    sys.path.append(os.path.abspath('.'))
    from app.models import Post
    from app.logical.media import convert_mp4_to_webp, convert_mp4_to_webm


def create_video_previews(overwrite, post_ids):
    query = Post.query.filter(Post.file_ext == 'mp4')
    if post_ids is not None:
        query = query.filter(Post.id.in_(post_ids))
    page = query.count_paginate(per_page=25)
    while True:
        print(f"\ncreate_animated_mp4_samples_and_previews: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            if overwrite or not os.path.exists(post.video_preview_path):
                print("\nCreating preview", post.shortlink)
                convert_mp4_to_webp(post.file_path, post.video_preview_path)
        if not page.has_next:
            break
        page = page.next()


def create_video_samples(overwrite, post_ids):
    query = Post.query.filter(Post.file_ext == 'mp4')
    if post_ids is not None:
        query = query.filter(Post.id.in_(post_ids))
    page = query.count_paginate(per_page=25)
    while True:
        print(f"\ncreate_animated_mp4_samples_and_previews: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            if overwrite or not os.path.exists(post.video_sample_path):
                print("\nCreating sample", post.shortlink)
                convert_mp4_to_webm(post.file_path, post.video_sample_path, post.width, post.height)
        if not page.has_next:
            break
        page = page.next()


def main(args):
    post_ids = [int(id) for id in args.id.split(',')] if args.id is not None else None
    if args.type == 'both' or args.type == 'preview':
        create_video_previews(args.overwrite, post_ids)
    if args.type == 'both' or args.type == 'sample':
        create_video_samples(args.overwrite, post_ids)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to generate animated mp4 previews and samples.")
    parser.add_argument('type', choices=['both', 'sample', 'preview'],
                        help="Choose which type of animated images to generate.")
    parser.add_argument('--id', required=False, help="A single ID or list of IDs (comma separated).")
    parser.add_argument('--overwrite', required=False, default=False, action="store_true",
                        help="Will overwite existing files.")
    args = parser.parse_args()

    initialize()
    main(args)
