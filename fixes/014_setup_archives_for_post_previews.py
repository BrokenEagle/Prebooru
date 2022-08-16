# FIXES/009_SETUP_ARCHIVES_FOR_POST_PREVIEWS.PY

# ## PYTHON IMPORTS
import os
import sys
from PIL import Image


# ## FUNCTIONS

def initialize():
    global ArchiveData, MEDIA_DIRECTORY, TEMP_DIRECTORY, create_directory, move_file, create_preview,\
        create_video_screenshot, put_get_raw, delete_file, check_alpha, convert_alpha
    sys.path.append(os.path.abspath('.'))
    from app.models import ArchiveData
    from app.logical.media import create_preview, create_video_screenshot, check_alpha, convert_alpha
    from config import MEDIA_DIRECTORY, TEMP_DIRECTORY
    from utility.file import create_directory, move_file, delete_file, put_get_raw


def main():
    query = ArchiveData.query.filter(ArchiveData.type == 'post')
    page = query.count_paginate(per_page=25)
    while True:
        print(f"setup_archives_for_post_previews: {page.first} - {page.last} / Total({page.count})")
        for archive in page.items:
            filename = archive.data_key + '.' + archive.data['body']['file_ext']
            old_path = os.path.join(MEDIA_DIRECTORY, 'archive', filename)
            if os.path.exists(old_path):
                print("Moving", archive.shortlink)
                create_directory(archive.file_path)
                print('\t', old_path, '->', archive.file_path)
                move_file(old_path, archive.file_path, True)
            if archive.data['body']['file_ext'] in ['jpg', 'png', 'gif']:
                image = Image.open(archive.file_path)
                if check_alpha(image):
                    image = convert_alpha(image)
            elif archive.data['body']['file_ext'] == 'mp4':
                save_path = os.path.join(TEMP_DIRECTORY, archive.data_key + '.' + 'jpg')
                create_video_screenshot(archive.file_path, save_path)
                image = Image.open(save_path)
                delete_file(save_path)
            print("Creating preview:", archive.preview_path)
            create_preview(image, archive.preview_path)
        if not page.has_next:
            break
        page = page.next()


# ##EXECUTION START

if __name__ == '__main__':
    initialize()
    main()
