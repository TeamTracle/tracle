import random

from backend import ffmpeg

def get_random_timestamps(duration):
    offset = 0.1
    timestamps = []
    for x in range(3):
        timestamps.append(abs(((x+1)-0.5)* duration/3))
    return timestamps

def get_video_duration(video):
    media_info = ffmpeg.ffprobe(video.uploaded_file.storage.local.path(video.uploaded_file.name))
    return float(media_info['format']['duration'])

def create_posters(video):
    duration  = get_video_duration(video)
    timestamps = get_random_timestamps(duration)
    print(timestamps)
    posters = []
    for timestamp in timestamps:
        posters.append(ffmpeg.create_poster(video.uploaded_file.storage.local.path(video.uploaded_file.name), timestamp))
    return posters
