from django.urls import path

from . import views

urlpatterns = [
	path('like', views.LikeView.as_view(), name='api_like'),
	path('dislike', views.DislikeView.as_view(), name='api_dislike'),
	path('subscribe', views.SubscribeView.as_view(), name='api_subscribe'),
	path('incrementviews', views.IncrementViewsView.as_view(), name='api_incrementviews'),
	path('videos/<channel_id>', views.VideoViewSet.as_view({'get' : 'list'}), name='api_videos_from_channel'),
]