import os
from app.models import Post
from utility.file import copy_file

WORKING_DIRECTORY = "C:\\Users\\Justin\\PrebooruData\\media"
ALTERNATE_DIRECTORY = "H:\\Prebooru\\Main"

def copy_files():
    while True:
        post_id = input("Enter post ID: ")
        if post_id.isdigit():
            is_alternate = False
            post = Post.find(int(post_id))
            filename = post.md5 + '.' + post.file_ext
            file_path = os.path.join(WORKING_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
            if not os.path.exists(file_path):
                file_path = os.path.join(ALTERNATE_DIRECTORY, 'data', post._partial_file_path + post.file_ext)
                if os.path.exists(file_path):
                    is_alternate = True
                else:
                    print("Unable to copy file!")
                    continue
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
        elif len(post_id) == 0:
            break

copy_files()
