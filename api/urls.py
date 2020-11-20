from django.urls import path

from . import views

urlpatterns = [
	path('like', views.LikeView.as_view(), name='api_like'),
	path('dislike', views.DislikeView.as_view(), name='api_dislike'),
	path('subscribe', views.SubscribeView.as_view(), name='api_subscribe'),
	path('incrementviews', views.IncrementViewsView.as_view(), name='api_incrementviews'),
	path('videos', views.VideoUploadView.as_view(), name='api_video_upload'),
	path('videos/tickets', views.VideoTicketView.as_view(), name='api_video_tickets'),
	path('videos/edit/<watch_id>', views.VideoEditView.as_view(), name='api_video_edit'),
	path('videos/status/<watch_id>', views.VideoStatusView.as_view(), name='api_video_status'),
	path('videos/<channel_id>', views.VideoViewSet.as_view({'get' : 'list'}), name='api_videos_from_channel'),
	path('uploadavatar', views.UploadAvatarView.as_view(), name='api_upload_avatar'),
	path('comments/like', views.CommentLikeView.as_view(), name='api_comment_like'),
	path('comments/dislike', views.CommentDislikeView.as_view(), name='api_comment_dislike'),
	path('comments/tickets', views.CommentTicketView.as_view(), name='api_comment_tickets'),
	path('comments/<watch_id>', views.CommentView.as_view(), name='api_comments'),
	path('subscriptions', views.SubscriptionsView.as_view(), name='api_subscriptions'),
	path('notifications', views.NotificationsView.as_view(), name='api_notifications_unread'),
	path('admin/ban_user', views.BanUser.as_view(), name='api_ban_user'),
]