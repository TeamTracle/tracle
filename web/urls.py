from django.urls import path, re_path

from . import views

urlpatterns = [
	path('', views.HomeView.as_view(), name='web_home'),
	path('signup', views.SignupView.as_view(), name='web_signup'),
	path('signin', views.SigninView.as_view(), name='web_signin'),
	path('signout', views.SignoutView.as_view(), name='web_signout'),
	path('watch', views.WatchView.as_view(), name='web_watch'),
	path('forgot-password', views.ResetPasswordView.as_view(), name='web_forgot_password'),
	path('forgot-password-confirm/<uidb64>/<token>/', views.ResetPasswordConfirmView.as_view(), name='web_password_reset_confirm'),
	re_path(r'^(?P<key>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.ActivateView.as_view(), name='web_activate'),
]