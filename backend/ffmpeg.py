import sys
import subprocess
import os
import tempfile

from django.core.files.base import ContentFile

from . import ffmpegprogress

def ffprobe(in_file):
	return ffmpegprogress.ffprobe(in_file)

def ffmpeg_callback(in_file, out_folder, vstats_path):
	cmd = [
		'ffmpeg',
		'-nostats', 
		'-loglevel', '0',
		'-y',
		'-vstats_file', vstats_path,
		'-i', in_file,
	]
	available_output_formats = {
		'360p' : [
			'-vf',
			'scale=w=640:h=360:force_original_aspect_ratio=decrease,pad=640:360:(ow-iw)/2:(oh-ih)/2',
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
		],
		'480p' : [
			'-vf',
			'scale=w=854:h=480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2',
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
		],
		'720p': [
			'-vf',
			'scale=w=1280:h=720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
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
	}
	selected_output_formats = ['360p', '480p']
	for output_format in selected_output_formats:
		cmd += available_output_formats[output_format]
	return subprocess.Popen(cmd).pid

def on_message_handler(percent, frame_count, total_frames, elapsed):
	sys.stdout.write('\r{:.2f}%'.format(percent))
	sys.stdout.flush()

def start_transcoding(video_instance):
	out_folder = os.path.join(video_instance.playlist_file.storage.local.location, str(video_instance.channel.channel_id), str(video_instance.watch_id))
	ffmpegprogress.start(video_instance.uploaded_file.path, out_folder, ffmpeg_callback, on_message=on_message_handler)
	master_playlist = '''
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=854x480
480p.m3u8
'''
	f = ContentFile(master_playlist)
	video_instance.playlist_file.save('playlist.m3u8', f)


def create_poster(in_file, timestamp, size=('854','480'), out_file=None):
    if not out_file:
        _, out_file = tempfile.mkstemp(suffix='.png')
    cmd = ['ffmpeg', '-ss', str(timestamp), '-i', in_file, '-vframes', '1', '-filter:v', 'scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2'.format(w=size[0], h=size[1]), '-y', out_file]
    p = subprocess.run(cmd, capture_output=True, universal_newlines=True)
    p.check_returncode()
    return out_file