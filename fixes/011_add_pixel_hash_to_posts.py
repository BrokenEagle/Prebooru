# FIXES/011_ADD_PIXEL_HASH_TO_POSTS.PY

# ## PYTHON IMPORTS
import os
import sys
from PIL import Image


# ## FUNCTIONS

def initialize():
    global SESSION, Post, get_buffer_checksum
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    from app.models import Post
    from utility.data import get_buffer_checksum


def main():
    query = Post.query.filter(Post.file_ext != 'mp4', Post.pixel_md5.is_(None))
    query = query.order_by(Post.id.asc())
    page = query.limit_paginate(per_page=100)
    while True:
        print(f"add_pixel_hash_to_posts: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            print(f"Processing {post.shortlink}")
            image = Image.open(post.file_path)
            data = image.tobytes()
            md5 = get_buffer_checksum(data)
            post.pixel_md5 = md5
            SESSION.commit()
        if not page.has_prev:
            break
        page = page.prev()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
