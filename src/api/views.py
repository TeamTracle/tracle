import secrets
from PIL import Image
from io import BytesIO
from django.conf import settings

from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile, File
from django.core.cache import cache
from django.utils import timezone
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from backend.utils import send_ban_notification_mail

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ModelSerializer

from .serializers import (
    OwnerVideoSerializer,
    VideoSerializer,
    VideoUploadSerializer,
    VideoEditSerializer,
    CommentSerializer,
    SubscriptionSerializer,
    NotificationSerializer,
)
from .permissions import IsAuthenticated, ReadOnly, IsSuperUser
from .exceptions import ChunkedUploadError

from backend.queries import (
    get_user,
    toggle_like,
    toggle_dislike,
    get_video,
    get_channel,
    toggle_subscription,
    get_channel_by_id,
    increment_view_count,
    get_image_by_pk,
    toggle_comment_like,
    toggle_comment_dislike,
    get_comment,
)
from backend.models import (
    BunnyVideo,
    ChunkedVideoUpload,
    Video,
    Comment,
    CommentTicket,
    VideoTicket,
    Subscription,
    Notification,
)


class LikeView(View):
    def get(self, request):
        return JsonResponse({"success": False, "error": "Operation not supported."})

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required."})

        watch_id = request.POST.get("watch_id", None)

        if not watch_id:
            return JsonResponse({"success": False, "error": "Missing watch_id"})

        video = get_video(watch_id)
        channel = get_channel(request.user)
        likes, dislikes = toggle_like(video, channel)

        return JsonResponse({"success": True, "likes": likes, "dislikes": dislikes})


class DislikeView(View):
    def get(self, request):
        return JsonResponse({"success": False, "error": "Operation not supported."})

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required."})

        watch_id = request.POST.get("watch_id", None)

        if not watch_id:
            return JsonResponse({"success": False, "error": "Missing watch_id."})

        video = get_video(watch_id)
        channel = get_channel(request.user)
        likes, dislikes = toggle_dislike(video, channel)

        return JsonResponse({"success": True, "likes": likes, "dislikes": dislikes})


class SubscribeView(View):
    def get(self, request):
        return JsonResponse({"success": False, "error": "Operation not supported."})

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required."})
        from_channel = get_channel(request.user)

        channel_id = request.POST.get("channel_id", None)
        if not channel_id:
            return JsonResponse({"success": False, "error": "Missing channel_id."})
        to_channel = get_channel_by_id(channel_id)
        if not to_channel:
            return JsonResponse({"success": False, "error": "Channel not found."})

        if from_channel.id == to_channel.id:
            return JsonResponse(
                {"success": False, "error": "Can not subscribe to self."}
            )

        subscriber_count = toggle_subscription(to_channel, from_channel)

        return JsonResponse({"success": True, "subscriber_count": subscriber_count})


class IncrementViewsView(View):
    def get(self, request):
        return JsonResponse({"success": False, "error": "Operation not supported."})

    def post(self, request):
        watch_id = request.POST.get("watch_id", None)
        if not watch_id:
            return JsonResponse({"success": False, "error": "Missing watch_id."})
        cache_key = f"{request.META.get('REMOTE_ADDR')}_{watch_id}"
        cache_result = cache.get(cache_key)
        if not cache_result:
            view_count = increment_view_count(watch_id)
            cache.set(cache_key, True)
        else:
            return JsonResponse({"success": False, "error": "Something went wrong!"})

        return JsonResponse({"success": True, "view_count": view_count})


class VideoViewSet(viewsets.ModelViewSet):
    def list(self, request, channel_id):
        channel = get_channel_by_id(channel_id)
        if not channel:
            return Response(
                {"message": "Channel not found."}, status=status.HTTP_400_BAD_REQUEST
            )

        orders = {
            "da": "-created",
            "dd": "created",
            "ta": "title",
            "td": "-title",
        }
        orderby = orders[request.query_params.get("order_by", "da")]

        if request.user.is_authenticated and channel == request.channel:
            self.queryset = Video.objects.filter(channel__exact=channel)
            self.queryset = self.queryset.annotate(
                num_likes=Count("likes"), num_dislikes=Count("dislikes")
            )
            self.queryset = self.queryset.order_by(orderby)
            self.queryset = self.paginate_queryset(self.queryset)
            serializer = OwnerVideoSerializer(self.queryset, many=True)
        else:
            self.queryset = Video.objects.public().filter(channel=channel)
            self.queryset = self.queryset.annotate(
                num_likes=Count("likes"), num_dislikes=Count("dislikes")
            )
            self.queryset = self.queryset.order_by(orderby)
            self.queryset = self.paginate_queryset(self.queryset)
            serializer = VideoSerializer(self.queryset, many=True)
        return self.get_paginated_response(serializer.data)


class UploadAvatarView(View):
    def post(self, request):
        channel = get_channel(request.user)
        in_file = request.FILES.get("avatar")
        out_file = BytesIO()
        in_image = Image.open(in_file)
        out_image = in_image.resize((144, 144))
        in_image.close()
        out_image.save(out_file, "PNG")
        channel.avatar.save(
            channel.channel_id + ".png", ContentFile(out_file.getvalue())
        )
        channel.avatar.storage.transfer(channel.avatar.name)
        channel.avatar.storage.local.delete(channel.avatar.name)
        result = {"success": "idk"}
        return JsonResponse(result)


class VideoEditView(APIView):
    permission_classes = [IsAuthenticated | ReadOnly]

    def get(self, request, watch_id):
        video = get_video(watch_id)
        serializer = VideoSerializer(video)
        serialized_data = serializer.data
        serialized_data["thumbnails"] = video.image_set.image_data()
        serialized_data["category"] = video.category_id
        serialized_data["channel"] = video.channel_id
        serialized_data["published"] = video.published
        serialized_data["visibility"] = video.visibility
        return Response(serialized_data)

    def put(self, request, watch_id):
        video = get_video(watch_id)
        if not request.channel == video.channel:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        serializer = VideoEditSerializer(data=request.data, instance=video)
        if serializer.is_valid():
            video = serializer.save()
            selectedThumbnail = request.data.get("selectedThumbnail", None)
            if selectedThumbnail and selectedThumbnail != "-1":
                img = get_image_by_pk(selectedThumbnail)
                img.toggle_primary()

            customthumbnail = request.FILES.get("customThumbnail", None)
            if customthumbnail:
                try:
                    video.add_custom_poster(customthumbnail.temporary_file_path())
                except IOError:
                    return Response(
                        "Something went wrong.", status=status.HTTP_400_BAD_REQUEST
                    )

            video.published = True
            video.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, watch_id):
        video = get_video(watch_id)
        if not video:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        if not request.channel == video.channel:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        res = video.delete()
        return Response(res)


class VideoUploadView(APIView):
    class Serializer(ModelSerializer):
        class Meta:
            fields = "__all__"
            model = ChunkedVideoUpload

    if settings.ALLOW_VIDEO_UPLOAD:
        permission_classes = [IsAuthenticated]
    else:
        permission_classes = [IsAdminUser]

    def get_response_data(self, chunked_upload, request):
        return self.Serializer(chunked_upload, context={"request": request}).data

    def is_valid_chunked_upload(self, chunked_upload):
        if chunked_upload.expired:
            raise ChunkedUploadError(
                status=status.HTTP_410_GONE, detail="Upload has expired"
            )
        if chunked_upload.status == ChunkedVideoUpload.UploadStatus.COMPLETE:
            raise ChunkedUploadError(
                status=status.HTTP_400_BAD_REQUEST,
                detail='Upload has already been marked as "complete"',
            )

    def _post_chunk(self, request, upload_id, whole=False, *args, **kwargs):
        try:
            chunk = request.data["file"]
        except KeyError:
            raise ChunkedUploadError(
                status=status.HTTP_400_BAD_REQUEST, detail="No chunk file was submitted"
            )

        chunk_size = int(request.data["chunk_size"])
        max_bytes = None  # TODO
        if max_bytes is not None and chunk_size > max_bytes:
            raise ChunkedUploadError(
                status=status.HTTP_400_BAD_REQUEST,
                details=f"Size of file exceeds the limit of {max_bytes} bytes",
            )

        if chunk_size != chunk.size:
            raise ChunkedUploadError(
                status=status.HTTP_400_BAD_REQUEST,
                detail=f"File size does not match: file size is {chunk.size} but {chunk_size} reported",
            )

        chunk_number = request.data["chunk_number"]
        total_chunks = request.data["total_chunks"]

        try:
            chunked_upload = ChunkedVideoUpload.objects.get(upload_id=upload_id)
            self.is_valid_chunked_upload(chunked_upload)
            chunked_upload.save_chunk(chunk, chunk_number, total_chunks)
        except ChunkedVideoUpload.DoesNotExist:
            raise ChunkedUploadError(
                status=status.HTTP_400_BAD_REQUEST, detail=chunked_upload.errors
            )

        return chunked_upload

    def post(self, request):
        request.data.update({"user": request.user.pk})
        upload_id = request.data.get("upload_id", None)
        try:
            chunked_upload = self._post_chunk(request, upload_id)
            return Response(
                self.get_response_data(chunked_upload, request),
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)
        except ChunkedUploadError as e:
            return Response(e.data, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        request.data.update({"user": request.user.pk})
        upload_id = request.data.get("upload_id")
        if upload_id is not None:
            try:
                chunked_upload = ChunkedVideoUpload.objects.get(upload_id=upload_id)
                chunked_upload.set_completed()
                uploaded_file = File(
                    file=chunked_upload.file.open(), name=str(chunked_upload.upload_id)
                )
                data = {
                    "uploaded_file": uploaded_file,
                    "channel": request.channel.pk,
                }
                video_serializer = VideoUploadSerializer(data=data)
                if video_serializer.is_valid():
                    video = video_serializer.save()
                    video.create_posters()
                    video.transcode()
                    serialized_data = video_serializer.data
                    serialized_data["thumbnails"] = video.image_set.image_data()
                    serialized_data["watch_id"] = video.watch_id
                    chunked_upload.delete()
                    return Response(serialized_data)
                else:
                    return Response(
                        video_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
            except ChunkedVideoUpload.DoesNotExist as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.Serializer(data=request.data)
        if serializer.is_valid():
            chunked_upload = serializer.save()
            return Response({"upload_id": chunked_upload.upload_id})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            instance = Video.objects.get(watch_id=request.data.get("watch_id"))
            if not request.channel == instance.channel:
                return Response(
                    "Something went wrong.", status=status.HTTP_400_BAD_REQUEST
                )
            serializer = VideoUploadSerializer(data=request.data, instance=instance)
            if serializer.is_valid():
                instance = serializer.save()

                selected_thumbnail = request.data.get("selectedThumbnail", None)
                if selected_thumbnail != "-1":
                    img = get_image_by_pk(selected_thumbnail)
                    img.toggle_primary()

                customThumbnail = request.FILES.get("customThumbnail", None)
                if customThumbnail:
                    try:
                        instance.add_custom_poster(
                            customThumbnail.temporary_file_path()
                        )
                    except IOError:
                        return Response(
                            "Something went wrong.", status=status.HTTP_400_BAD_REQUEST
                        )
            return Response(serializer.data)
        except Video.DoesNotExist as e:
            return Response(e, status=status.HTTP_404_NOT_FOUND)


class VideoStatusView(View):
    def get(self, request, watch_id):
        video = get_video(watch_id)
        status = video.transcode_status
        return JsonResponse({"status": status})


class CommentView(APIView):
    def get(self, request, watch_id):
        video = get_video(watch_id)
        if not video:
            return Response("Video not found.", status=status.HTTP_400_BAD_REQUEST)
        queryset = Comment.objects.filter(parent_id=None, video=video)
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, watch_id):
        print(request.data)
        video = get_video(watch_id)
        if not video:
            return Response("Video not found.", status=status.HTTP_400_BAD_REQUEST)
        text = request.data.get("text", None)
        if not text:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        if len(text) > 499:
            return Response(
                "Comment body too long.", status=status.HTTP_400_BAD_REQUEST
            )
        parent = None
        parent_id = request.data.get("parent_id", None)
        if parent_id:
            parent = Comment.objects.get(id=parent_id)
            if parent.parent:
                parent = parent.parent
        comment = Comment.objects.create(
            video=video, author=request.channel, text=text, parent=parent
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data)


class CommentLikeView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        comment_id = request.data.get("comment_id", None)
        if not comment_id:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        comment = Comment.objects.get(pk=comment_id)
        likes, dislikes = toggle_comment_like(comment, request.channel)
        return Response({"likes": likes, "dislikes": dislikes})


class CommentDislikeView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        comment_id = request.data.get("comment_id", None)
        if not comment_id:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)
        comment = Comment.objects.get(pk=comment_id)
        likes, dislikes = toggle_comment_dislike(comment, request.channel)
        return Response({"likes": likes, "dislikes": dislikes})


class CommentTicketView(APIView):
    permission_classes = [IsAuthenticated | ReadOnly]

    def post(self, request):
        comment = get_comment(request.data.get("comment_id", None))
        if not comment:
            return Response("Something went wrong.", status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get("reason", None)
        if not reason or reason == "null":
            return Response(
                {"message": "Please select a reason."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        body = request.data.get("body", "")
        CommentTicket.objects.create(
            comment=comment,
            channel=request.channel,
            body=body,
            reason=CommentTicket.Reason(reason),
        )
        return Response({})


class VideoTicketView(APIView):
    permission_classes = [IsAuthenticated | ReadOnly]

    def post(self, request):
        print(request.data)
        video = get_video(request.data.get("watch_id"))
        body = request.data.get("body", "")
        reason = request.data.get("reason", None)
        if not reason:
            return Response(
                {"message": "Please selet a reason."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        VideoTicket.objects.create(
            video=video, body=body, reason=reason, channel=request.channel
        )
        return Response({})


class SubscriptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Subscription.objects.filter(from_channel=request.channel)
        serializer = SubscriptionSerializer(queryset, many=True)
        return Response(serializer.data)


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status = request.GET.get("status")
        if status == "unread":
            queryset = request.user.notifications.unread().filter(
                recipient=request.user
            )
        else:
            queryset = request.user.notifications.all().filter(recipient=request.user)
        serializer = NotificationSerializer(queryset, many=True)
        data = {"unread_count": queryset.count(), "unread_list": serializer.data}
        return Response(data)

    def post(self, request):
        try:
            notification = Notification.objects.get(pk=request.data.get("id"))
        except Notification.DoesNotExist:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        notification.unread = False
        notification.save()
        return Response(request.data)

    def delete(self, request):
        print(request.GET.get("id"))
        try:
            notification = Notification.objects.get(pk=request.GET.get("id"))
        except Notification.DoesNotExist as e:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        notification.delete()
        return Response({})


class BanUser(APIView):
    permission_classes = [IsSuperUser]

    def post(self, request):
        pk = request.data.get("id", None)
        if pk:
            user = get_user(pk)
            user.banned = not user.banned
            user.banned_at = timezone.now()
            user.session_set.all().delete()
            user.save()
            if user.banned:
                send_ban_notification_mail(user)
            change_message = "banned" if user.banned else "unbanned"
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(user).pk,
                object_id=user.id,
                object_repr=str(user),
                action_flag=CHANGE,
                change_message=change_message,
            )
            return Response({})
        else:
            return Response(
                {"message": "Something went wrong."}, status=status.HTTP_400_BAD_REQUEST
            )


class BunnyCallback(APIView):
    def post(self, request):
        key = request.query_params.get("key", None)
        if key is None or not secrets.compare_digest(
            settings.BUNNYNET["callback_key"], key
        ):
            raise PermissionDenied(
                {"message": "You do not have permission to access this resource."}
            )
        guid = request.data["VideoGuid"]
        video_status = request.data["Status"]
        if video_status == 1:
            bvideo = BunnyVideo.objects.get(bunny_guid=guid)
            bvideo.status = BunnyVideo.TranscodeStatus.PROCESSING
            bvideo.save()
        elif video_status == 3:
            bvideo = BunnyVideo.objects.get(bunny_guid=guid)
            bvideo.status = BunnyVideo.TranscodeStatus.DONE
            bvideo.save()
        elif video_status == 5:
            bvideo = BunnyVideo.objects.get(bunny_guid=guid)
            bvideo.status = BunnyVideo.TranscodeStatus.ERROR
            bvideo.save()

        return Response({})
