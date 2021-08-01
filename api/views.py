import json
# video.image_set.image_data() os
# 
from PIL import Image
from io import BytesIO
from django.conf import settings

from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.core.cache import cache
from django.utils import timezone
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

import django_rq
from django_rq.jobs import Job

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import VideoSerializer, VideoUploadSerializer, VideoEditSerializer, CommentSerializer, SubscriptionSerializer, NotificationSerializer
from .permissions import IsAuthenticated, ReadOnly, IsSuperUser

from backend.queries import get_user, toggle_like, toggle_dislike, get_video, get_videos_from_channel, get_channel, toggle_subscription, get_channel_by_id, increment_view_count, get_image_by_pk, toggle_comment_like, toggle_comment_dislike, get_comment
from backend.models import BunnyVideo, Video, Comment, CommentLike, CommentTicket, VideoTicket, Subscription, Notification
from backend.models import Image as ImageModel
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
		if not to_channel:
			return JsonResponse({'success' : False, 'error' : 'Channel not found.'})

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
			if not channel:
				return Response({'message': 'Channel not found.'}, status=status.HTTP_400_BAD_REQUEST)
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
			if selectedThumbnail and selectedThumbnail != '-1':
				img = get_image_by_pk(selectedThumbnail)
				img.toggle_primary()

			customthumbnail = request.FILES.get('customThumbnail', None)
			if customthumbnail:
				try:
					in_image = Image.open(customthumbnail.temporary_file_path())
					out_file = BytesIO()
					in_image.thumbnail((854, 480))
					old_size = in_image.size
					new_size = (854,480)
					new_image = Image.new('RGB', new_size)
					new_image.paste(in_image, (int((new_size[0]-old_size[0])/2), int((new_size[1]-old_size[1])/2)))
					new_image.save(out_file, 'PNG')
					in_image.close()

					image = ImageModel.objects.create(image_set=video.image_set, video=video)
					image.image.save('poster.png', ContentFile(out_file.getvalue()))
					image.toggle_primary()

				except IOError:
					return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)

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
		instance = Video.objects.get(watch_id=request.data.get('watch_id'))
		if not request.channel == instance.channel:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)

		serializer = VideoUploadSerializer(data=request.data, instance=instance)
		if serializer.is_valid():
			instance = serializer.save()
			instance.published = True
			instance.save(update_fields=['published'])

			selectedThumbnail = request.data.get('selectedThumbnail', None)
			if selectedThumbnail != '-1': 
				img = get_image_by_pk(selectedThumbnail)
				img.toggle_primary()
			
			customthumbnail = request.FILES.get('customThumbnail', None)
			if customthumbnail:
				try:
					in_image = Image.open(customthumbnail.temporary_file_path())
					
					out_file = BytesIO()
					in_image.thumbnail((854, 480))
					old_size = in_image.size
					new_size = (854,480)
					new_image = Image.new('RGB', new_size)
					new_image.paste(in_image, (int((new_size[0]-old_size[0])/2), int((new_size[1]-old_size[1])/2)))
					new_image.save(out_file, 'PNG')
					in_image.close()

					image = ImageModel.objects.create(image_set=instance.image_set, video=instance)
					image.image.save('poster.png', ContentFile(out_file.getvalue()))
					image.toggle_primary()

				except IOError:
					return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)


			return Response(serializer.data)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoStatusView(View):
	def get(self, request, watch_id):
		video = get_video(watch_id)
		status = video.transcode_status
		return JsonResponse({'status' : status})

class CommentView(APIView):
	def get(self, request, watch_id):
		video = get_video(watch_id)
		if not video:
			return Response('Video not found.', status=status.HTTP_400_BAD_REQUEST)
		queryset = Comment.objects.filter(parent_id=None, video=video)
		serializer = CommentSerializer(queryset, many=True)
		return Response(serializer.data)

	def post(self, request, watch_id):
		print(request.data)
		video = get_video(watch_id)
		if not video:
			return Response('Video not found.', status=status.HTTP_400_BAD_REQUEST)
		text = request.data.get('text', None)
		if not text:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		if len(text) > 499:
			return Response('Comment body too long.', status=status.HTTP_400_BAD_REQUEST)
		parent = None
		parent_id = request.data.get('parent_id', None)
		if parent_id:
			parent = Comment.objects.get(id=parent_id)
			if parent.parent:
				parent = parent.parent
		comment = Comment.objects.create(video=video, author=request.channel, text=text, parent=parent)
		serializer = CommentSerializer(comment)
		return Response(serializer.data)


class CommentLikeView(APIView):
	permission_classes = [IsAuthenticated,]

	def post(self, request):
		comment_id = request.data.get('comment_id', None)
		if not comment_id:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		comment = Comment.objects.get(pk=comment_id)
		likes, dislikes = toggle_comment_like(comment, request.channel)
		return Response({'likes' : likes, 'dislikes' : dislikes})

class CommentDislikeView(APIView):
	permission_classes = [IsAuthenticated,]

	def post(self, request):
		comment_id = request.data.get('comment_id', None)
		if not comment_id:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)
		comment = Comment.objects.get(pk=comment_id)
		likes, dislikes = toggle_comment_dislike(comment, request.channel)
		return Response({'likes' : likes, 'dislikes' : dislikes})

class CommentTicketView(APIView):
	permission_classes = [IsAuthenticated|ReadOnly]

	def post(self, request):
		comment = get_comment(request.data.get('comment_id', None))
		if not comment:
			return Response('Something went wrong.', status=status.HTTP_400_BAD_REQUEST)

		reason = request.data.get('reason', None)
		if not reason or reason == 'null':
			return Response({'message' : 'Please select a reason.'}, status=status.HTTP_400_BAD_REQUEST)

		body = request.data.get('body', '')
		ct = CommentTicket.objects.create(comment=comment, channel=request.channel, body=body, reason=CommentTicket.Reason(reason))
		return Response({})

class VideoTicketView(APIView):
	permission_classes = [IsAuthenticated|ReadOnly]

	def post(self, request):
		print(request.data)
		video = get_video(request.data.get('watch_id'))
		body = request.data.get('body', '')
		reason = request.data.get('reason', None)
		if not reason:
			return Response({'message' : 'Please selet a reason.'}, status=status.HTTP_400_BAD_REQUEST)
		vt = VideoTicket.objects.create(video=video, body=body, reason=reason, channel=request.channel)
		return Response({})

class SubscriptionsView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		queryset = Subscription.objects.filter(from_channel=request.channel)
		serializer =  SubscriptionSerializer(queryset, many=True)
		return Response(serializer.data)

class NotificationsView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		status = request.GET.get('status')
		if status == 'unread':
			queryset = request.user.notifications.unread().filter(recipient=request.user)
		else:
			queryset = request.user.notifications.all().filter(recipient=request.user) 
		serializer = NotificationSerializer(queryset, many=True)
		data = {
			'unread_count' : queryset.count(),
			'unread_list' : serializer.data 
		}
		return Response(data)

	def post(self, request):
		try:
			notification = Notification.objects.get(pk=request.data.get('id'))
		except Notification.DoesNotExist as e:
			return Response({}, status=status.HTTP_400_BAD_REQUEST)
		notification.unread = False
		notification.save()
		return Response(request.data)

	def delete(self, request):
		print(request.GET.get('id'))
		try:
			notification = Notification.objects.get(pk=request.GET.get('id'))
		except Notification.DoesNotExist as e:
			return Response({}, status=status.HTTP_400_BAD_REQUEST)
		notification.delete()
		return Response({})

class BanUser(APIView):
	permission_classes = [IsSuperUser]

	def post(self, request):
		pk = request.data.get('id', None)
		if pk:
			user = get_user(pk)
			user.banned = not user.banned
			user.banned_at = timezone.now()
			user.session_set.all().delete()
			user.save()
			change_message = 'banned' if user.banned else 'unbanned'
			LogEntry.objects.log_action(user_id=request.user.id, content_type_id=ContentType.objects.get_for_model(user).pk, object_id=user.id, object_repr=str(user), action_flag=CHANGE, change_message=change_message)
			return Response({})
		else:
			return Response({'message': 'Something went wrong.'}, status=status.HTTP_400_BAD_REQUEST)

#TODO: Improve access restriction
class BunnyCallback(APIView):
	def post(self, request):
		if not request.META['REMOTE_ADDR'] == settings.BUNNYNET['callback_remote']:
			return Response({}, status=status.HTTP_400_BAD_REQUEST)
		guid = request.data['VideoGuid']
		status = request.data['Status']
		if status == 3:
			bvideo = BunnyVideo.objects.get(bunny_guid=guid)
			bvideo.status = BunnyVideo.TranscodeStatus.DONE
			bvideo.save()
		elif status == 4:
			bvideo = BunnyVideo.objects.get(bunny_guid=guid)
			bvideo.status = BunnyVideo.TranscodeStatus.PROCESSING
			bvideo.save()

		return Response({})