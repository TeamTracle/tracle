import os
import subprocess
import tempfile
import base64
import random

from backend.models import get_media_location

def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, universal_newlines=True)
    if p.returncode != 0:
        print(p.stderr)
    return p

def create_thumbnail(in_file, timestamp, size='0', out_file=None):
    if not out_file:
        _, out_file = tempfile.mkstemp(suffix='.png')
    cmd = ['ffmpegthumbnailer', '-i', in_file, '-o', out_file, '-t', str(timestamp), '-s', str(size)]
    p = _run(cmd)
    return out_file


def get_preview_thumbnails(file_path):
    thumbnails = []
    for i in range(3):
        timestamp = int(random.random()*100)
        image_path = create_thumbnail(file_path, timestamp, size='150')
        with open(image_path, 'rb') as f:
            blob = base64.b64encode(f.read())
        thumbnails.append({'timestamp' : timestamp, 'file' : 'data:image/png;base64,' + blob.decode('utf-8')})

    return thumbnails

def get_thumbnails(instance, timestamps, selected_timestamp):
    thumbnails = []
    fsmedia = instance.get_media_fs()
    for i in range(3):
        timestamp = timestamps[i]
        tmp_image_path = create_thumbnail(instance.uploaded_file.path, timestamp)
        with open(tmp_image_path, 'rb') as f:
            image_path = fsmedia.save('thumbnail_{}.png'.format(i), f)
        if str(timestamp) == str(selected_timestamp):
            instance.thumbnail = image_path
            instance.save()

    return thumbnails

def video_transcode_task(video):
    print('Start encoding')
    print(video.watch_id)
    in_file = video.uploaded_file.path
    print(in_file)
    out_folder = get_media_location(video.channel.channel_id, video.watch_id)
    os.makedirs(out_folder, exist_ok=True)
    cmd = ['ffmpeg', '-hide_banner', '-y']
    cmd += [
        '-i', in_file,
        '-vf',
        'scale=w=640:h=360:force_original_aspect_ratio=decrease',
        '-c:a', 'aac',
        '-ar', '48000',
        '-c:v', 'h264',
        '-profile:v', 'main',
        '-crf', '20',
        '-sc_threshold', '0',
        '-g', '48',
        '-keyint_min', '48',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-b:v', '800k',
        '-maxrate', '856k',
        '-bufsize', '1200k',
        '-b:a', '96k',
        '-hls_segment_filename', '{}/360p_%03d.ts'.format(out_folder),
        '{}/360p.m3u8'.format(out_folder)
    ]
    cmd += [
        '-vf',
        'scale=w=842:h=480:force_original_aspect_ratio=decrease',
        '-c:a', 'aac',
        '-ar', '48000',
        '-c:v', 'h264',
        '-profile:v', 'main',
        '-pix_fmt', 'yuv420p',
        '-crf', '20',
        '-sc_threshold', '0',
        '-g', '48',
        '-keyint_min', '48',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-b:v', '1400k',
        '-maxrate', '1498k',
        '-bufsize', '2100k',
        '-b:a', '128k',
        '-hls_segment_filename', '{}/480p_%03d.ts'.format(out_folder),
        '{}/480p.m3u8'.format(out_folder)
    ]
    cmd += [
        '-vf',
        'scale=w=1280:h=720:force_original_aspect_ratio=decrease',
        '-c:a', 'aac',
        '-ar', '48000',
        '-c:v', 'h264',
        '-profile:v', 'main',
        '-pix_fmt', 'yuv420p',
        '-crf', '20',
        '-sc_threshold', '0',
        '-g', '48',
        '-keyint_min', '48',
        '-hls_time', '4',
        '-hls_playlist_type', 'vod',
        '-b:v', '2800k',
        '-maxrate', '2996k',
        '-bufsize', '4200k',
        '-b:a', '128k',
        '-hls_segment_filename', '{}/720p_%03d.ts'.format(out_folder),
        '{}/720p.m3u8'.format(out_folder)
    ]

    p = _run(cmd)
      # -vf scale=w=1920:h=1080:force_original_aspect_ratio=decrease -c:a aac -ar 48000 -c:v h264 -profile:v main -crf 20 -sc_threshold 0 -g 48 -keyint_min 48 -hls_time 4 -hls_playlist_type vod -b:v 5000k -maxrate 5350k -bufsize 7500k -b:a 192k -hls_segment_filename beach/1080p_%03d.ts beach/1080p.m3u8
    master_playlist = '''
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=842x480
480p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p.m3u8
'''
    with open(os.path.join(out_folder, 'playlist.m3u8'), 'w') as f:
        f.write(master_playlist)

    video.refresh_from_db()
    video.processed = True
    video.status = 'finished'
    video.save(update_fields=['processed', 'status'])
    print('encoding done')

