from time import sleep
from . import ffmpeg

from django.conf import settings

def video_transcode_task(video=None):
	print('TRANSCODING VIDEO...')
	transcoded_video = video.transcoded_video
	transcoded_video.status = transcoded_video.TranscodeStatus.PROCESSING
	transcoded_video.save()
	try:
		ffmpeg.start_transcoding(video)
		transcoded_video.status = transcoded_video.TranscodeStatus.DONE
		transcoded_video.save()
		print('TRANSCODING DONE!')
	except Exception as e:
		transcoded_video.status = transcoded_video.TranscodeStatus.ERROR
		transcoded_video.save()
		print(e)
		print('TRANSCODING FAILED!')
		raise e

	if settings.BUNNYCDN.get('enabled'):
		print('UPLOADING FILES...')
		try:
			video.transfer_files()
			print('UPLOADING DONE!')
		except Exception as e:
			print(e)
			print('UPLOADING FAILED!')
