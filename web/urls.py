from django.urls import path, re_path

from . import views

urlpatterns = [
	path('', views.HomeView.as_view(), name='web_home'),
	path('terms', views.TermsView.as_view(), name='web_terms'),
	path('guidelines', views.GuidelinesView.as_view(), name='web_guidelines'),
	path('signup', views.SignupView.as_view(), name='web_signup'),
	path('signin', views.SigninView.as_view(), name='web_signin'),
	path('signout', views.SignoutView.as_view(), name='web_signout'),
	path('watch', views.WatchView.as_view(), name='web_watch'),
	path('channel/<channel_id>', views.ChannelView.as_view(), name='web_channel'),
	path('channels', views.ChannelsView.as_view(), name='web_channels'),
	path('upload', views.UploadVideoView.as_view(), name='web_upload_video'),
	path('dashboard', views.DashboardBaseView.as_view(), name='web_dashboard'),
	path('dashboard/settings', views.DashboardSettingsView.as_view(), name='web_dashboard_settings'),
	path('dashboard/videos', views.DashboardVideosView.as_view(), name='web_dashboard_videos'),
	path('dashboard/videos/<watch_id>', views.DashboardEditVideoView.as_view(), name='web_dashboard_edit_video'),
	path('dashboard/subscriptions', views.SubscriptionsView.as_view(), name='web_dashboard_subscriptions'),
	path('inbox/notifications', views.InboxNotifications.as_view(), name='web_inbox_notifications'),
	path('forgot-password', views.ResetPasswordView.as_view(), name='web_forgot_password'),
	path('forgot-password-confirm/<uidb64>/<token>/', views.ResetPasswordConfirmView.as_view(), name='web_password_reset_confirm'),
	re_path(r'^(?P<key>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.ActivateView.as_view(), name='web_activate'),
]