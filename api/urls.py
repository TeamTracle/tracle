from django.urls import path

from . import views

urlpatterns = [
	path('like', views.LikeView.as_view(), name='api_like'),
	path('dislike', views.DislikeView.as_view(), name='api_dislike'),
	path('subscribe', views.SubscribeView.as_view(), name='api_subscribe'),
	path('incrementviews', views.IncrementViewsView.as_view(), name='api_incrementviews'),
	path('videos', views.VideoUploadView.as_view(), name='api_video_upload'),
	path('videos/edit/<watch_id>', views.VideoEditView.as_view(), name='api_video_edit'),
	path('videos/status/<watch_id>', views.VideoStatusView.as_view(), name='api_video_status'),
	path('videos/<channel_id>', views.VideoViewSet.as_view({'get' : 'list'}), name='api_videos_from_channel'),
	path('uploadavatar', views.UploadAvatarView.as_view(), name='api_upload_avatar'),
]