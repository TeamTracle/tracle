from time import sleep
from . import ffmpeg

from bunnyapi import VideosApi

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

def bunnyvideo_upload_task(bunny_video=None):
	vapi = VideosApi(settings.BUNNYNET['access_token'], settings.BUNNYNET['library_id'])
	vobj = vapi.create_video(bunny_video.video.watch_id)
	bunny_video.bunny_guid = vobj['guid']
	bunny_video.save()
	try:
		local_path = bunny_video.video.uploaded_file.path
		vapi.upload_video(bunny_video.bunny_guid, local_path)
		bunny_video.video.transfer_files()
	except NotImplementedError:
		url = f'https://storage.bunnycdn.com/{settings.BUNNYCDN["storage_zone_name"]}/{video.uploaded_file.name}'
		vapi.fetch_video(bunny_video.bunny_guid, url, fetch_headers={'headers' : {'AccessKey' : settings.BUNNYCDN['access_token']}})
