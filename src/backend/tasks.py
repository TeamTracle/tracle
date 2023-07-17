from bunnyapi import VideosApi

from django.conf import settings

from backend.models import BunnyVideo


def bunnyvideo_upload_task(bunny_video: BunnyVideo):
    vapi = VideosApi(settings.BUNNYNET["access_token"], settings.BUNNYNET["library_id"])
    vobj = vapi.create_video(bunny_video.video.watch_id)
    bunny_video.bunny_guid = vobj["guid"]
    bunny_video.save()
    url = f'https://storage.bunnycdn.com/{settings.BUNNYCDN["storage_zone_name"]}/{bunny_video.video.uploaded_file.name}'  # noqa E501
    vapi.fetch_video(
        bunny_video.bunny_guid,
        url,
        fetch_headers={"headers": {"AccessKey": settings.BUNNYCDN["access_token"]}},
    )
