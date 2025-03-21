import os
import colorama
from app.models import Post
from utility.file import delete_file
from utility.uprint import print_info

WORKING_DIRECTORY = "C:\\Users\\Justin\\PrebooruData\\media\\"
ALTERNATE_DIRECTORY = "H:\\Prebooru\\Main"

def delete_files():
    page = Post.query.filter(Post.id <= 338772).count_paginate(per_page=100)
    while True:
        print_info(f"check_posts: {page.first} - {page.last} / Total({page.count})")
        print(page.items[0].id, end="", flush=True)
        for post in page.items:
            base_directory = None
            file_path = os.path.join(WORKING_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
            alternate_path = os.path.join(ALTERNATE_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
            if os.path.exists(file_path):
                print('.', end="", flush=True)
                base_directory = WORKING_DIRECTORY
            elif os.path.exists(alternate_path):
                print(':', end="", flush=True)
                base_directory = ALTERNATE_DIRECTORY
                file_path = alternate_path
            else:
                print('-', end="", flush=True)
                continue
            #print("Deleting", post.shortlink, file_path)
            #input()
            delete_file(file_path)
            if post.has_sample:
                file_path = os.path.join(base_directory, 'sample', post._partial_file_path + 'jpg')
                delete_file(file_path)
            if post.has_preview:
                file_path = os.path.join(base_directory, 'preview', post._partial_file_path + 'jpg')
                delete_file(file_path)
        print(page.items[-1].id, end="", flush=True)
        print('\n', end="", flush=True)
        if not page.has_next:
            break
        page = page.next()

colorama.init(autoreset=True)
delete_files()
