import os
import colorama
from app.models import Post
from utility.file import copy_file, put_get_raw
from utility.data import get_buffer_checksum
from utility.uprint import print_info, print_warning

WORKING_DIRECTORY = "C:\\Users\\Justin\\PrebooruData\\media\\"
ALTERNATE_DIRECTORY = "H:\\Prebooru\\Main"

def check_posts():
    page = Post.query.limit_paginate(per_page=100)
    while True:
        print_info(f"check_posts: {page.first} - {page.last} / Total({page.count})")
        print(page.items[0].id, end="", flush=True)
        for post in page.items:
            if not os.path.exists(post.file_path):
                print("\nData missing:", post.shortlink)
                key = input("Copy file? ")
                if len(key):
                    copy_post(post)
                continue
            buffer = put_get_raw(post.file_path, 'rb')
            checksum = get_buffer_checksum(buffer)
            if checksum != post.md5:
                print("MD5 checksum mismatch:", post.shortlink)
                print("%s != %s" % (checksum, post.md5))
                input("BREAK")
            if post.has_sample and not os.path.exists(post.sample_path):
                print("Sample missing:", post.shortlink)
                input("BREAK")
            if post.has_preview and not os.path.exists(post.preview_path):
                print("Preview missing:", post.shortlink)
                input("BREAK")
            print('.', end="", flush=True)
        print(page.items[-1].id, end="", flush=True)
        print('\n', end="", flush=True)
        if not page.has_next:
            break
        page = page.next()

def copy_post(post):
    is_alternate = False
    filename = post.md5 + '.' + post.file_ext
    file_path = os.path.join(WORKING_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
    if not os.path.exists(file_path):
        file_path = os.path.join(ALTERNATE_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
        if os.path.exists(file_path):
            is_alternate = True
        else:
            print("Unable to copy file!")
            return
    copy_file(file_path, post.file_path)
    print(file_path, '->', post.file_path)
    if post.has_sample:
        file_path = os.path.join(WORKING_DIRECTORY if not is_alternate else ALTERNATE_DIRECTORY, 'sample', post._partial_file_path + 'jpg')
        if os.path.exists(file_path):
            copy_file(file_path, post.sample_path)
            print(file_path, '->', post.sample_path)
        else:
            print("Unable to copy sample file!")
    if post.has_preview:
        file_path = os.path.join(WORKING_DIRECTORY if not is_alternate else ALTERNATE_DIRECTORY, 'preview', post._partial_file_path + 'jpg')
        if os.path.exists(file_path):
            copy_file(file_path, post.preview_path)
            print(file_path, '->', post.preview_path)
        else:
            print("Unable to copy preview file!")

colorama.init(autoreset=True)
check_posts()
