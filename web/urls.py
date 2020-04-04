from django.urls import path, re_path

from . import views

urlpatterns = [
	path('', views.HomeView.as_view(), name='web_home'),
	path('signup', views.SignupView.as_view(), name='web_signup'),
	path('signin', views.SigninView.as_view(), name='web_signin'),
	path('signout', views.SignoutView.as_view(), name='web_signout'),
	path('watch', views.WatchView.as_view(), name='web_watch'),
	re_path(r'^(?P<key>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.ActivateView.as_view(), name='web_activate'),
]