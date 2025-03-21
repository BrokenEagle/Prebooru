import os

from utility.file import *

WORKING_DIRECTORY = 'C:\\Users\\Justin\\GitHub\\ai_setup\\storage\\media\\sample\\'

dirs = get_subdirectory_listing(WORKING_DIRECTORY)

for dir in dirs:
    print(dir, end="", flush=True)
    dirpath = os.path.join(WORKING_DIRECTORY, dir)
    subdirs = get_subdirectory_listing(dirpath)
    for subdir in subdirs:
        subdirpath = os.path.join(dirpath, subdir)
        files = get_directory_listing(subdirpath)
        for file in files:
            ext = get_file_extension(file)
            if ext != 'jpg':
                newname = no_file_extension(file) + '.jpg'
                os.rename(os.path.join(subdirpath, file), os.path.join(subdirpath, newname))
                print('.', end="", flush=True)
        print(':', end="", flush=True)
    print('\n', end="", flush=True)
