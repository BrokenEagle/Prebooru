# APP/LOGICAL/MEDIA.PY

# ## PYTHON IMPORTS
import os
import cv2
import uuid
import ffmpeg
from PIL import Image
from io import BytesIO

# ## PACKAGE IMPORTS
from config import TEMP_DIRECTORY, PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS, MP4_SKIP_FRAMES, MP4_MIN_FRAMES,\
    WEBP_QUALITY, WEBP_LOOPS
from utility.file import create_directory, delete_directory, delete_file, put_get_raw
from utility.data import get_buffer_checksum


# ## GLOBAL VARIABLES

MILLISECONDS_PER_SECOND = 1000


# ## FUNCTIONS

def check_alpha(image):
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        try:
            channel = image.getchannel('A')
        except Exception:
            print("Error getting Alpha channel... assuming transparency present.")
            return True
        else:
            return any(pixel for pixel in channel.getdata() if pixel < 255)
    return False


def convert_alpha(image):
    alpha = image.copy().convert('RGBA').getchannel('A')
    bg = Image.new('RGBA', image.size, (255, 255, 255, 255))
    bg.paste(image, mask=alpha)
    return bg


def get_pixel_hash(image):
    data = image.tobytes()
    return get_buffer_checksum(data)


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


def convert_mp4_to_webp(file_path, save_path):
    capture_directory = os.path.join(TEMP_DIRECTORY, str(uuid.uuid4()))
    print("Opening ->", file_path)
    create_directory(capture_directory, True)
    video_capture = cv2.VideoCapture(file_path)
    frame_rate = video_capture.get(cv2.CAP_PROP_FPS)
    frame_count = video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
    skip_frames = MP4_SKIP_FRAMES if frame_count > MP4_MIN_FRAMES else 1
    duration = int(MILLISECONDS_PER_SECOND / (frame_rate / skip_frames))  # milliseconds
    frame_count = 0
    files = []
    print("Saving frames")
    while True:
        if (frame_count % skip_frames) == 0:
            still_reading, image_array = video_capture.read()
            if still_reading:
                file = 'cv2tmp-%04d.jpg' % frame_count
                cv2.imwrite(os.path.join(capture_directory, file), image_array)
                files.append(file)
        else:
            still_reading = video_capture.grab()
        if not still_reading:
            break
        frame_count += 1
    print("Opening captured images")
    frames = [Image.open(os.path.join(capture_directory, file)) for file in files]
    if frames[0].width > PREVIEW_DIMENSIONS[0] or frames[1].height > PREVIEW_DIMENSIONS[1]:
        print("Converting to thumbnails")
        for frame in frames:
            frame.thumbnail(PREVIEW_DIMENSIONS)
    print("Saving to WEBP ->", save_path)
    create_directory(save_path)
    frames[0].save(save_path, 'webp', append_images=frames[1:], save_all=True, duration=duration, loop=WEBP_LOOPS,
                   minimize_size=True, lossless=False, quality=WEBP_QUALITY)
    print("Cleaning capture directory")
    for file in files:
        delete_file(os.path.join(capture_directory, file))
    delete_directory(capture_directory)


def convert_mp4_to_webm(file_path, save_path, width=None, height=None):
    output_options = {
        'vcodec': 'libvpx',
        'video_bitrate': '250k',
        'audio_bitrate': '20k',
        'crf': 50,
        'y': None,
    }
    if width is not None and height is not None:
        scale_video = False
        if width > SAMPLE_DIMENSIONS[0]:
            divisor = width / SAMPLE_DIMENSIONS[0]
            height /= divisor
            scale_video = True
        if height > SAMPLE_DIMENSIONS[1]:
            divisor = height / SAMPLE_DIMENSIONS[1]
            width /= divisor
            scale_video = True
        if scale_video:
            width = int(width)
            height = int(height)
            output_options['vf'] = f"scale={width}:{height}"
    print("Creating video sample media->", save_path)
    create_directory(save_path)
    stream = ffmpeg.input(file_path)
    stream = stream.output(save_path, **output_options)
    print("Command:", stream.compile(), '\n')
    try:
        stream.run(quiet=True)
    except Exception as e:
        msg = "Exception creating video sample media: %s" % str(e)
        print(msg)
        return msg
