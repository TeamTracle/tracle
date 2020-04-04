from django.urls import path

from . import views

urlpatterns = [
	path('like', views.LikeView.as_view(), name='api_like'),
	path('dislike', views.DislikeView.as_view(), name='api_dislike'),
	path('subscribe', views.SubscribeView.as_view(), name='api_subscribe'),
]