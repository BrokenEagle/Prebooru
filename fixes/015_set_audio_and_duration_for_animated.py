# FIXES/015_SET_AUDIO_AND_DURATION_FOR_ANIMATED.PY

# ## PYTHON IMPORTS
import os
import sys
from argparse import ArgumentParser
import colorama


# ## FUNCTIONS

def initialize():
    global print_warning, Post, update_post_from_parameters, get_video_info
    sys.path.append(os.path.abspath('.'))
    from utility.print import print_warning
    from app.models import Post
    from app.logical.database.post_db import update_post_from_parameters
    from app.logical.media import get_video_info
    colorama.init(autoreset=True)


def update_video_fields(fields, post_ids):
    query = Post.query.filter(Post.file_ext == 'mp4')
    if post_ids is not None:
        query = query.filter(Post.id.in_(post_ids))
    page = query.count_paginate(per_page=25)
    while True:
        print(f"\nupdate_video_fields: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            vinfo = get_video_info(post.file_path)
            if isinstance(vinfo, str):
                print_warning(post.shortlink, ':', vinfo)
                continue
            updateparams = {k: d for (k, d) in vinfo.items() if k in fields}
            update_post_from_parameters(post, updateparams)
        if not page.has_next:
            break
        page = page.next()


def main(args):
    post_ids = [int(id) for id in args.id.split(',')] if args.id is not None else None
    fields = ['audio', 'duration'] if args.type == 'both' else args.type
    update_video_fields(fields, post_ids)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to generate set audio and/or duration on animated files.")
    parser.add_argument('type', choices=['both', 'audio', 'duration'],
                        help="Choose which type of field to update.")
    parser.add_argument('--id', required=False, help="A single ID or list of IDs (comma separated).")
    args = parser.parse_args()

    initialize()
    main(args)
