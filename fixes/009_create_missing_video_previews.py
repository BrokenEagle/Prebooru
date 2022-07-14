# FIXES/009_CREATE_MISSING_VIDEO_PREVIEWS.PY

# ## PYTHON IMPORTS
import os
import sys
import shutil


# ## FUNCTIONS

def initialize():
    global Post, create_directory
    sys.path.append(os.path.abspath('.'))
    from app.models import Post
    from utility.file import create_directory


def main():
    query = Post.query.filter(Post.file_ext == 'mp4', Post.width <= 300, Post.height <= 300)
    page = query.count_paginate(per_page=100)
    while True:
        print(f"create_missing_video_previews: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            if not os.path.exists(post.preview_path):
                print("Copying", post.shortlink)
                create_directory(post.preview_path)
                shutil.copyfile(post.sample_path, post.preview_path)
        if not page.has_next:
            break
        page = page.next()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
