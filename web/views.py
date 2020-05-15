from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

from backend.forms import SignupForm, SigninForm, ResetPasswordForm, SetPasswordForm, ChangeUserForm, VideoDetailsForm
from backend.queries import get_latest_videos, get_all_categories, get_category, get_channel, get_video, is_video_liked, is_video_disliked, is_subscribed, get_user, get_videos_from_channel, get_channel_by_id, get_total_views
from .tokens import account_activation_token

class HomeView(View):
    def get(self, request):
        videos = get_latest_videos()
        category_slug = request.GET.get('c', None)
        if category_slug:
            category = get_category(category_slug)
            videos = videos.filter(category__exact=category)
        categories = get_all_categories()
        return render(request, 'web/home.html', {'videos' : videos, 'categories' : categories})

class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'web/signup.html', {'form' : form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            subject = 'Activate your TRACLE Account!'
            context = {
                'user' : user,
                'domain' : settings.DOMAIN,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            }
            message = render_to_string('web/email_confirm_account.html', context)
            user.email_user(subject, message)
            return render(request, 'web/verification_sent.html')
        return render(request, 'web/signup.html', {'form' : form})

class ActivateView(View):

    def get(self, request, key, token):
        try:
            uid = force_text(urlsafe_base64_decode(key))
            user = get_user(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.email_confirmed = True
            user.save()
            return redirect('web_signin')
        else:
            return render(request, 'web/account_activation_invalid.html')

class SigninView(View):
    def get(self, request):
        form = SigninForm()
        return render(request, 'web/signin.html', {'form' : form})

    def post(self, request):
        form = SigninForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=raw_password)
            if user is not None:
                login(request, user)
                channel = get_channel(user)
                request.session['channel_id'] =  channel.channel_id
                request.session['channel_name'] = channel.name
                avatar = '/static/web/img/avatar.png'
                if channel.avatar:
                    avatar = channel.avatar.url
                request.session['channel_avatar'] = avatar

                return redirect('web_home')
        return render(request, 'web/signin.html', {'form' : form})

class SignoutView(View):
    def get(self, request):
        logout(request)
        return redirect('web_home')

class ResetPasswordView(PasswordResetView):
    template_name = 'web/forgot_password.html'
    email_template_name = 'web/forgot_password_email.html'
    domain = settings.DOMAIN
    form_class = ResetPasswordForm
    success_url = '/'

class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'web/forgot_password_confirm.html'
    form_class = SetPasswordForm
    success_url = '/signin'

class WatchView(View):
    def get(self, request):
        watch_id = request.GET.get('v', None)
        video = get_video(watch_id)
        videos = get_latest_videos()
        is_liked = False
        is_disliked = False
        subscribed = False
        if request.user.is_authenticated:
            channel = get_channel(request.user)
            is_liked = is_video_liked(video, channel)
            is_disliked = is_video_disliked(video, channel)
            subscribed = is_subscribed(video.channel, channel)

        rating = video.likes.count() + video.dislikes.count()
        if rating > 0:
            likebar_value = (100 / rating) * video.likes.count()
        else:
            likebar_value = 50

        return render(request, 'web/watch.html', {'video' : video, 'is_liked' : is_liked, 'is_disliked': is_disliked, 'likebar_value' : likebar_value, 'is_subscribed' : subscribed, 'videos' : videos})

class DashboardBaseView(LoginRequiredMixin, View):
    login_url = '/signin'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        return redirect('web_dashboard_videos')

class DashboardSettingsView(DashboardBaseView):

    def get(self, request):
        channel = get_channel(request.user)
        form = ChangeUserForm({'email' : request.user.email, 'channel_name' : channel.name})
        return render(request, 'web/dashboard_account.html', {'form' : form, 'channel' : channel})

    def post(self, request):
        channel = get_channel(request.user)
        form = ChangeUserForm({'email' : request.user.email, 'channel_name' : request.POST.get('channel_name')})
        context = {'form' : form, 'channel' : channel}
        if form.is_valid():
            form.save(channel)
        return render(request, 'web/dashboard_account.html', context)

class DashboardVideosView(DashboardBaseView):

    def get(self, request):
        return render(request, 'web/dashboard_videos.html')

class DashboardEditVideoView(DashboardBaseView):
    def get(self, request, watch_id):
        video = get_video(watch_id)
        form = VideoDetailsForm(instance=video)
        return render(request, 'web/dashboard_edit_video.html', {'video' : video, 'form' : form})

    def post(self, request, watch_id):
        video = get_video(watch_id)
        form = VideoDetailsForm(request.POST, instance=video)
        if form.is_valid():
            form.save()
            return JsonResponse({'success' : True})

        return JsonResponse({'success' : False})

class ChannelView(View):
    def get(self, request, channel_id):
        channel = get_channel_by_id(channel_id)
        total_views = get_total_views(channel)
        subscribed = False
        if request.user.is_authenticated:
            subscribed = is_subscribed(channel, get_channel(request.user))
        return render(request, 'web/channel.html', {'channel' : channel, 'is_subscribed' : subscribed, 'total_views' : total_views})