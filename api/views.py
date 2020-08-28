import json
# video.image_set.image_data() os
# 
from PIL import Image
from io import BytesIO

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.cache import cache

import django_rq
from django_rq.jobs import Job

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import VideoSerializer, VideoUploadSerializer, VideoEditSerializer
from .permissions import IsAuthenticated, ReadOnly

from backend.queries import toggle_like, toggle_dislike, get_video, get_videos_from_channel, get_channel, toggle_subscription, get_channel_by_id, increment_view_count, get_image_by_pk
from backend.models import Video
from backend.forms import VideoDetailsForm


class LikeView(View):
	def get(self, request):
		return JsonResponse({'success' : False, 'error' : 'Operation not supported.'})

	def post(self, request):
		if not request.user.is_authenticated:
			return JsonResponse({'success' : False, 'error' : 'Authentication required.'})

		watch_id = request.POST.get('watch_id', None)

		if not watch_id:
			return JsonResponse({'success' : False, 'error' : 'Missing watch_id'})

		video = get_video(watch_id)
		channel = get_channel(request.user)
		likes, dislikes = toggle_like(video, channel)

		return JsonResponse({'success' : True, 'likes': likes, 'dislikes': dislikes})

class DislikeView(View):
	def get(self, request):
		return JsonResponse({'success' : False, 'error' : 'Operation not supported.'})

	def post(self, request):
		if not request.user.is_authenticated:
			return JsonResponse({'success' : False, 'error' : 'Authentication required.'})

		watch_id = request.POST.get('watch_id', None)

		if not watch_id:
			return JsonResponse({'success' : False, 'error' : 'Missing watch_id.'})
		
		video = get_video(watch_id)
		channel = get_channel(request.user)
		likes, dislikes = toggle_dislike(video, channel)

		return JsonResponse({'success' : True, 'likes' : likes, 'dislikes': dislikes})

class SubscribeView(View):
	def get(self, request):
		return JsonResponse({'success' : False, 'error' : 'Operation not supported.'})

	def post(self, request):
		if not request.user.is_authenticated:
			return JsonResponse({'success' : False, 'error' : 'Authentication required.'})
		from_channel = get_channel(request.user)

		channel_id = request.POST.get('channel_id', None)
		if not channel_id:
			return JsonResponse({'success' : False, 'error' : 'Missing channel_id.'})
		to_channel = get_channel_by_id(channel_id) 

		if from_channel.id == to_channel.id:
			return JsonResponse({'success' : False, 'error' : 'Can not subscribe to self.'})

		subscriber_count = toggle_subscription(to_channel, from_channel)

		return JsonResponse({'success' : True, 'subscriber_count' : subscriber_count})

class IncrementViewsView(View):
	def get(self, request):
		return JsonResponse({'success' : False, 'error' : 'Operation not supported.'})

	def post(self, request):
		watch_id = request.POST.get('watch_id', None)
		if not watch_id:
			return JsonResponse({'success' : False, 'error' : 'Missing watch_id.'})
		cache_key = f"{request.META.get('REMOTE_ADDR')}_{watch_id}"
		cache_result = cache.get(cache_key)
		if not cache_result:
			view_count = increment_view_count(watch_id)
			cache.set(cache_key, True)
		else:
			return JsonResponse({'success' : False, 'error' : 'Something went wrong!'})

		return JsonResponse({'success' : True, 'view_count' : view_count})

class VideoViewSet(viewsets.ModelViewSet):
		def list(self, request, channel_id):
			channel = get_channel_by_id(channel_id)
			queryset = Video.objects.filter(channel__exact=channel)
			serializer = VideoSerializer(queryset, many=True)
			return Response(serializer.data)

class UploadAvatarView(View):
	def post(self, request):
		channel = get_channel(request.user)
		in_file = request.FILES.get('avatar')
		out_file = BytesIO()
		in_image = Image.open(in_file)
		out_image = in_image.resize((144, 144))
		in_image.close()
		out_image.save(out_file, 'PNG')
		channel.avatar.save('avatars/' + channel.channel_id + '.png', ContentFile(out_file.getvalue()))
		result = {'success' : 'idk'}
		return JsonResponse(result)

class VideoEditView(APIView):
	permission_classes = [IsAuthenticated|ReadOnly]

	def get(self, request, watch_id):
		video = get_video(watch_id)
		serializer = VideoSerializer(video)
		serialized_data = serializer.data
		serialized_data['thumbnails'] = video.image_set.image_data()
		serialized_data['category'] = video.category_id
		serialized_data['channel'] = video.channel_id
		return Response(serialized_data)

	def put(self, request, watch_id):
		video = get_video(watch_id)
		if not request.channel == video.channel:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		serializer = VideoEditSerializer(data=request.data, instance=video)
		if serializer.is_valid():
			video = serializer.save()
			selectedThumbnail = request.data.get('selectedThumbnail', None)
			if selectedThumbnail: 
				img = get_image_by_pk(selectedThumbnail)
				img.toggle_primary()
			video.published = True
			video.save()
			return Response(serializer.data)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def delete(self, request, watch_id):
		video = get_video(watch_id)
		if not video:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		if not request.channel == video.channel:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		res = video.delete()
		return Response(res)

class VideoUploadView(APIView):
	permission_classes = [IsAuthenticated|ReadOnly]

	def post(self, request):
		request.data.update({'channel' : request.channel.pk})
		serializer = VideoUploadSerializer(data=request.data)
		if serializer.is_valid():
			video = serializer.save()
			# job = django_rq.enqueue(video_transcode_task, video=video)
			# video.job_id = job.id
			# video.status = job.get_status()
			video.save()
			video.create_posters()
			video.transcode()
			serialized_data = serializer.data
			serialized_data['thumbnails'] = video.image_set.image_data()
			serialized_data['watch_id'] = video.watch_id
			return Response(serialized_data)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def put(self, request):
		print(request.data)
		instance = Video.objects.get(watch_id=request.data.get('watch_id'))
		if not request.channel == instance.channel:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		serializer = VideoUploadSerializer(data=request.data, instance=instance)
		if serializer.is_valid():
			instance = serializer.save()
			instance.published = True
			instance.visibility = instance.VisibilityStatus.PUBLIC
			selectedThumbnail = request.data.get('selectedThumbnail', None)
			if selectedThumbnail: 
				img = get_image_by_pk(selectedThumbnail)
				img.toggle_primary()
			instance.save(update_fields=['published', 'visibility'])
			return Response(serializer.data)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoStatusView(View):
	def get(self, request, watch_id):
		video = get_video(watch_id)
		status = video.transcode_status
		return JsonResponse({'status' : status})