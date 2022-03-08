# APP/LOGICAL/MEDIA.PY

# ## PYTHON IMPORTS
import ffmpeg
from PIL import Image
from io import BytesIO

# ## PACKAGE IMPORTS
from config import PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from utility.file import create_directory, put_get_raw


# ## FUNCTIONS

def load_image(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return "Error processing image data: %s" % repr(e)
    return image


def create_preview(image, preview_path, downsample=True):
    try:
        preview = image.copy().convert("RGB")
        if downsample:
            preview.thumbnail(PREVIEW_DIMENSIONS)
        create_directory(preview_path)
        print("Saving preview:", preview_path)
        preview.save(preview_path, "JPEG")
    except Exception as e:
        return "Error creating preview: %s" % repr(e)


def create_sample(image, sample_path, downsample=True):
    try:
        sample = image.copy().convert("RGB")
        if downsample:
            sample.thumbnail(SAMPLE_DIMENSIONS)
        create_directory(sample_path)
        print("Saving sample:", sample_path)
        sample.save(sample_path, "JPEG")
    except Exception as e:
        return "Error creating sample: %s" % repr(e)


def create_data(buffer, file_path):
    create_directory(file_path)
    print("Saving data:", file_path)
    try:
        put_get_raw(file_path, 'wb', buffer)
    except Exception as e:
        return "Error creating data: %s" % repr(e)


def create_video_screenshot(file_path, save_path):
    print("Saving video screenshot:", save_path)
    try:
        ffmpeg.input(file_path, ss=0).output(save_path, vframes=1).run()
    except Exception as e:
        return "Error creating video screenshot: %s" % repr(e)
