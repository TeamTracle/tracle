from time import sleep
from . import ffmpeg

from django.conf import settings

def video_transcode_task(video=None):
	print('TRANSCODING VIDEO...')
	video.refresh_from_db()
	video.transcode_status = video.TranscodeStatus.PROCESSING
	video.save(update_fields=['transcode_status'])
	try:
		ffmpeg.start_transcoding(video)
		video.refresh_from_db()
		video.transcode_status = video.TranscodeStatus.DONE
		video.save(update_fields=['transcode_status'])
		print('TRANSCODING DONE!')
	except Exception as e:
		video.refresh_from_db()
		video.transcode_status = video.TranscodeStatus.ERROR
		video.save(update_fields=['transcode_status'])
		video.delete_local_files()
		print(e)
		print('TRANSCODING FAILED!')
		return

	if settings.BUNNYCDN.get('enabled'):
		print('UPLOADING FILES...')
		try:
			video.transfer_files()
			print('UPLOADING DONE!')
		except Exception as e:
			print(e)
			print('UPLOADING FAILED!')
