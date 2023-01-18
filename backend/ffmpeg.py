import sys
import subprocess
import os
import tempfile

from django.core.files.base import ContentFile

def ffprobe(infile):
    """ffprobe front-end."""
    return json.loads(
        sp.check_output([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
            '-show_streams', infile
        ], encoding='utf-8'))

def create_poster(in_file, timestamp, size=('854','480'), out_file=None):
    if not out_file:
        _, out_file = tempfile.mkstemp(suffix='.png')
    cmd = ['ffmpeg', '-ss', str(timestamp), '-i', in_file, '-vframes', '1', '-filter:v', 'scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2'.format(w=size[0], h=size[1]), '-y', out_file]
    p = subprocess.run(cmd, capture_output=True, universal_newlines=True)
    p.check_returncode()
    return out_file