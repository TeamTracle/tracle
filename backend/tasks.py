from bunnyapi import VideosApi

from django.conf import settings

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
		url = f'https://storage.bunnycdn.com/{settings.BUNNYCDN["storage_zone_name"]}/{bunny_video.video.uploaded_file.name}'
		vapi.fetch_video(bunny_video.bunny_guid, url, fetch_headers={'headers' : {'AccessKey' : settings.BUNNYCDN['access_token']}})
