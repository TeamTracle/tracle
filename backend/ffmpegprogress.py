"""
This is based on ffmpeg-progress.py
https://github.com/Tatsh/ffmpeg-progress/blob/v0.0.4/ffmpeg_progress.py
"""
from datetime import datetime
from os.path import basename, splitext
from tempfile import mkstemp
from time import sleep
import json
import os
import re
import subprocess as sp
import sys

import psutil

__all__ = ['ffprobe', 'start']

linesep_bytes = os.linesep.encode('utf-8')


def ffprobe(infile):
    """ffprobe front-end."""
    return json.loads(
        sp.check_output([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
            '-show_streams', infile
        ], encoding='utf-8'))


def default_on_message(percent, fr_cnt, total_frames, elapsed):
    bar = list('|' + (20 * ' ') + '|')
    to_fill = int(round((fr_cnt / total_frames) * 20)) or 1
    for x in range(1, to_fill):
        bar[x] = '░'
    bar[to_fill] = '░'
    s_bar = ''.join(bar)
    sys.stdout.write('\r{}  {:5.1f}%   {:d} / {:d} frames;   '
                     'elapsed time: {:.2f} seconds'.format(
                         s_bar, percent, fr_cnt, total_frames, elapsed))
    sys.stdout.flush()


def display(total_frames,
            vstats_fd,
            pid,
            on_message=None,
            wait_time=1.0):
    start = datetime.now()
    fr_cnt = 0
    elapsed = percent = 0.0
    if not on_message:
        on_message = default_on_message
    while fr_cnt < total_frames and percent < 100.0:
        sleep(wait_time)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
            break
        try:
            pos_end = os.lseek(vstats_fd, -2, os.SEEK_END)
        except OSError:
            continue  # Not enough data in file
        pos_start = None
        while os.read(vstats_fd, 1) != linesep_bytes:
            pos_start = os.lseek(vstats_fd, -2, os.SEEK_CUR)
        if pos_start is None:
            continue
        last = os.read(vstats_fd, pos_end - pos_start).decode('utf-8').strip()
        try:
            vstats = int(re.split(r'\s+', last)[5])
        except IndexError:
            vstats = 0
        if vstats > fr_cnt:
            fr_cnt = vstats
            percent = 100 * (fr_cnt / total_frames)
        elapsed = (datetime.now() - start).total_seconds()
        on_message(percent, fr_cnt, total_frames, elapsed)


def start(infile,
          out_folder,
          ffmpeg_func,
          on_message=None,
          on_done=None,
          index=0,
          wait_time=1.0,
          initial_wait_time=2.0):
    probe = ffprobe(infile)
    for s in probe['streams']:
        if s['codec_type'] == 'video':
            index = s['index']
    try:
        probe['streams'][index]
    except (IndexError, KeyError):
        raise ValueError('Probe failed')
    try:
        fps = eval(probe['streams'][index]['avg_frame_rate'])
    except ZeroDivisionError:
        raise ValueError('Cannot use input FPS')
    if fps == 0:
        raise ValueError('Unexpected zero FPS')
    dur = float(probe['format']['duration'])
    total_frames = int(dur * fps)
    if total_frames <= 0:
        raise ValueError('Unexpected total frames value')
    prefix = 'ffprog-{}'.format(splitext(basename(infile))[0])
    vstats_fd, vstats_path = mkstemp(suffix='.vstats', prefix=prefix)
    pid = ffmpeg_func(infile, out_folder, vstats_path)
    if not pid:
        raise TypeError('ffmpeg callback must return a valid PID')
    sleep(initial_wait_time)
    display(total_frames,
            vstats_fd,
            pid,
            wait_time=wait_time,
            on_message=on_message)
    os.close(vstats_fd)
    if on_done:
        on_done()
