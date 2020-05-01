import json

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core import serializers

from rest_framework import viewsets
from rest_framework.response import Response

from .serializers import VideoSerializer
from backend.queries import toggle_like, toggle_dislike, get_video, get_videos_from_channel, get_channel, toggle_subscription, get_channel_by_id, increment_view_count

from backend.models import Video 

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

		subscriber_count = toggle_subscription(to_channel, from_channel)

		return JsonResponse({'success' : True, 'subscriber_count' : subscriber_count})

class IncrementViewsView(View):
	def get(self, request):
		return JsonResponse({'success' : False, 'error' : 'Operation not supported.'})

	def post(self, request):
		watch_id = request.POST.get('watch_id', None)
		if not watch_id:
			return JsonResponse({'success' : False, 'error' : 'Missing watch_id.'})
		view_count = increment_view_count(watch_id)

		return JsonResponse({'success' : True, 'view_count' : view_count})

class VideoViewSet(viewsets.ModelViewSet):
		def list(self, request, channel_id):
			channel = get_channel_by_id(channel_id)
			queryset = Video.objects.filter(channel__exact=channel)
			serializer = VideoSerializer(queryset, many=True)
			return Response(serializer.data)