from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.clickjacking import (
    xframe_options_sameorigin,
    xframe_options_exempt,
)
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse

from backend.forms import (
    SignupForm,
    SigninForm,
    ResetPasswordForm,
    SetPasswordForm,
    ChangeUserForm,
    VideoDetailsForm,
    ChannelBackgroundForm,
)
from backend import queries
from backend.models import ChannelBackground, WatchHistory, User
from .tokens import account_activation_token
from backend.utils import send_confirmation_mail

import logging

logger = logging.getLogger()


def page_not_found_view(request, exception=None):
    return render(request, "web/error/404.html", status=404)


def server_error_view(request, exception=None):
    return render(request, "web/error/500.html", status=500)


class HomeView(View):
    def get(self, request):
        categories = queries.get_all_categories()
        context = {"categories": categories, "selected_category": None}

        category_slug = request.GET.get("c", None)
        if not category_slug:
            videos = queries.get_latest_videos()

        else:
            if category_slug == "subscriptions":
                videos = queries.get_sub_feed(request.channel)
                context["selected_category"] = {
                    "title": "Subscriptions",
                    "icon": "fa-list",
                    "slug": "subscriptions",
                }
            elif category_slug == "trending":
                videos = queries.get_trending_videos()
                context["selected_category"] = {
                    "title": "Trending",
                    "icon": "fa-chart-bar",
                    "slug": "trending",
                }
            else:
                category = queries.get_category(category_slug)
                videos = queries.get_videos_from_category(category)
                context["selected_category"] = category

        context["videos"] = videos

        page_number = request.GET.get("p", 1)
        paginator = Paginator(context["videos"], 20)
        context["videos"] = paginator.get_page(page_number)

        context["recommended_videos"] = queries.get_top_videos()

        return render(request, "web/home.html", context)


class ResultsView(View):
    def get(self, request):
        categories = queries.get_all_categories()
        search_terms = request.GET.get("search_terms", "")
        videos = queries.filter_by_search_terms(search_terms)
        return render(
            request,
            "web/results.html",
            {"search_terms": search_terms, "categories": categories, "videos": videos},
        )


class TermsView(View):
    def get(self, request):
        return render(request, "web/terms.html")


class GuidelinesView(View):
    def get(self, request):
        return render(request, "web/guidelines.html")


class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, "web/signup.html", {"form": form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            send_confirmation_mail(user)
            return render(request, "web/verification_sent.html")
        return render(request, "web/signup.html", {"form": form})


class ActivateView(View):
    def get(self, request, key, token):
        try:
            uid = force_text(urlsafe_base64_decode(key))
            user = queries.get_user(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.email_confirmed = True
            user.save()
            return redirect("web_signin")
        else:
            return render(request, "web/account_activation_invalid.html")


class SigninView(View):
    def get(self, request):
        form = SigninForm()
        return render(request, "web/signin.html", {"form": form})

    def post(self, request):
        form = SigninForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get("password")
            user: User = authenticate(username=email, password=raw_password)  # type: ignore
            if user is not None:
                login(request, user)
                user.update_last_login(request.META.get("REMOTE_ADDR"))
                channel = queries.get_channel(user)
                channel.update_last_login()
                return redirect(request.GET.get("redirect_to", "web_home"))
        return render(request, "web/signin.html", {"form": form})


class SignoutView(View):
    def get(self, request):
        logout(request)
        return redirect("web_home")


class ResetPasswordView(PasswordResetView):
    template_name = "web/forgot_password.html"
    form_class = ResetPasswordForm
    success_url = "/"

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())


class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = "web/forgot_password_confirm.html"
    form_class = SetPasswordForm
    success_url = "/signin"


class WatchView(View):
    def get(self, request):
        recommended_videos = queries.get_recommended_videos()
        watch_id = request.GET.get("v", None)
        video = queries.get_published_video_or_none(watch_id)

        if not video:
            return render(
                request,
                "web/watch.html",
                {
                    "error": "Video unavailable",
                    "recommended_videos": recommended_videos,
                },
            )
        if video.visibility == video.VisibilityStatus.PRIVATE:
            if request.user.is_authenticated:
                if not request.channel == video.channel:
                    return render(
                        request,
                        "web/watch.html",
                        {
                            "error": "This video is private",
                            "recommended_videos": recommended_videos,
                        },
                    )
            else:
                return render(
                    request,
                    "web/watch.html",
                    {
                        "error": "This video is private",
                        "recommended_videos": recommended_videos,
                    },
                )

        if video.get_transcoded_video().status != "finished":
            return render(
                request,
                "web/watch.html",
                {
                    "video": video,
                    "error": "This video has not finished processing yet",
                    "recommended_videos": recommended_videos,
                },
            )

        if video.videostrike_set.exists():
            return render(
                request,
                "web/watch.html",
                {
                    "video": video,
                    "error": "Video blocked due to violation of our ToS and/or Guidelines",
                    "recommended_videos": recommended_videos,
                },
            )

        is_liked = False
        is_disliked = False
        subscribed = False
        if request.user.is_authenticated:
            channel = queries.get_channel(request.user)
            is_liked = queries.is_video_liked(video, channel)
            is_disliked = queries.is_video_disliked(video, channel)
            subscribed = queries.is_subscribed(video.channel, channel)

            WatchHistory.objects.add_entry(channel, video)

        rating = video.likes.count() + video.dislikes.count()
        if rating > 0:
            likebar_value = (100 / rating) * video.likes.count()
        else:
            likebar_value = 50

        return render(
            request,
            "web/watch.html",
            {
                "video": video,
                "is_liked": is_liked,
                "is_disliked": is_disliked,
                "likebar_value": likebar_value,
                "is_subscribed": subscribed,
                "recommended_videos": recommended_videos,
            },
        )


class WatchEmbedView(View):
    @xframe_options_exempt
    def get(self, request, watch_id):
        video = queries.get_published_video_or_none(watch_id)
        if not video or video.visibility == video.VisibilityStatus.PRIVATE:
            return render(request, "web/embed.html")
        return render(request, "web/embed.html", {"video": video})


class DashboardBaseView(LoginRequiredMixin, View):
    login_url = "/signin"
    redirect_field_name = "redirect_to"

    def get(self, request):
        return redirect("web_dashboard_videos")


class DashboardSettingsView(DashboardBaseView):
    def get(self, request):
        channel = queries.get_channel(request.user)
        form = ChangeUserForm(
            {
                "email": request.user.email,
                "channel_name": channel.name,
                "description": channel.description,
            }
        )
        return render(
            request, "web/dashboard_account.html", {"form": form, "channel": channel}
        )

    def post(self, request):
        channel = queries.get_channel(request.user)
        form = ChangeUserForm(
            {
                "email": request.user.email,
                "channel_name": request.POST.get("channel_name"),
                "description": request.POST.get("description"),
            }
        )
        context = {"form": form, "channel": channel}
        if form.is_valid():
            form.save(channel)
        return render(request, "web/dashboard_account.html", context)


class DashboardVideosView(DashboardBaseView):
    def get(self, request):
        return render(request, "web/dashboard_videos.html")


class DashboardEditVideoView(DashboardBaseView):
    def get(self, request, watch_id):
        return render(request, "web/dashboard_edit_video.html", {"watch_id": watch_id})


class SubscriptionsView(DashboardBaseView):
    def get(self, request):
        return render(request, "web/dashboard_subscriptions.html")


class ChannelVideosView(View):
    @xframe_options_sameorigin
    def get(self, request, channel_id):
        channel = queries.get_channel_by_id(channel_id)
        if not channel:
            return render(request, "web/channel_videos.html", {})
        total_views = queries.get_total_views(channel)
        subscribed = False
        if request.user.is_authenticated:
            subscribed = queries.is_subscribed(
                channel, queries.get_channel(request.user)
            )
        videos = queries.get_videos_from_channel(channel)
        ordering = request.GET.get("sort", "da")
        if ordering == "da":
            videos = videos.order_by("-created")
        elif ordering == "dd":
            videos = videos.order_by("created")
        elif ordering == "p":
            videos = videos.order_by("-views")

        video_count = videos.count()

        page_number = request.GET.get("p", 1)
        paginator = Paginator(videos, 20)
        videos = paginator.get_page(page_number)

        return render(
            request,
            "web/channel_videos.html",
            {
                "channel": channel,
                "is_subscribed": subscribed,
                "total_views": total_views,
                "videos": videos,
                "selected_tab": "videos",
                "ordering": ordering,
                "video_count": video_count,
            },
        )


class ChannelFeaturedView(View):
    @xframe_options_sameorigin
    def get(self, request, channel_id):
        channel = queries.get_channel_by_id(channel_id)
        if not channel:
            return render(request, "web/channel_featured.html", {})
        total_views = queries.get_total_views(channel)
        subscribed = False
        if request.user.is_authenticated:
            subscribed = queries.is_subscribed(
                channel, queries.get_channel(request.user)
            )
        qs = queries.get_videos_from_channel(channel)
        if qs:
            featured_video = qs.order_by("-views")[0]
        else:
            featured_video = None
        return render(
            request,
            "web/channel_featured.html",
            {
                "channel": channel,
                "is_subscribed": subscribed,
                "total_views": total_views,
                "selected_tab": "featured",
                "video": featured_video,
            },
        )


class ChannelFeedView(View):
    @xframe_options_sameorigin
    def get(self, request, channel_id):
        channel = queries.get_channel_by_id(channel_id)
        filter = request.GET.get("filter", "2")
        if not channel:
            return render(request, "web/channel_feed.html", {})
        total_views = queries.get_total_views(channel)
        subscribed = False
        if request.user.is_authenticated:
            subscribed = queries.is_subscribed(
                channel, queries.get_channel(request.user)
            )

        if filter == "1":
            all_qs = [video.target_actions.public() for video in channel.videos.all()]  # type: ignore
            if all_qs:
                stream = all_qs[0].union(*all_qs)
                stream = stream.order_by("-timestamp")
            else:
                stream = []
        else:
            from actstream.models import actor_stream

            stream = actor_stream(channel)
            stream = stream.exclude(verb="commented")
        return render(
            request,
            "web/channel_feed.html",
            {
                "channel": channel,
                "is_subscribed": subscribed,
                "total_views": total_views,
                "selected_tab": "feed",
                "filter": filter,
                "stream": stream,
            },
        )


class ChannelEditorView(LoginRequiredMixin, View):
    login_url = "/signin"
    redirect_field_name = "redirect_to"

    def get(self, request):
        try:
            form = ChannelBackgroundForm(instance=request.channel.background)
        except ChannelBackground.DoesNotExist:
            form = ChannelBackgroundForm()
        return render(request, "web/channel_editor.html", {"form": form})

    def post(self, request):
        if request.POST.get("delete", None):
            try:
                cb = request.channel.background.desktop_image.delete()
                return JsonResponse({"message": "Deleted desktop background"})
            except Exception:  # TODO: Be more specific
                return JsonResponse({"message": "Something went wrong. :("})

        try:
            form = ChannelBackgroundForm(
                request.POST, request.FILES, instance=request.channel.background
            )
        except ChannelBackground.DoesNotExist:
            form = ChannelBackgroundForm(request.POST, request.FILES)
        if form.is_valid():
            cb = form.save(commit=False)
            cb.channel = request.channel
            cb.save()
            if cb.desktop_image and cb.desktop_image.storage.local.exists(
                cb.desktop_image.name
            ):
                cb.desktop_image.storage.transfer(cb.desktop_image.name)
                cb.desktop_image.storage.local.delete(cb.desktop_image.name)
            return redirect("web_channel", channel_id=request.channel.channel_id)
        print(form.errors)
        return render(request, "web/channel_editor.html", {"form": form})


class ChannelsView(View):
    def get(self, request):
        channels = queries.get_all_channels()
        return render(request, "web/channels.html", {"channels": channels})


class UploadVideoView(LoginRequiredMixin, View):
    login_url = "/signin"
    redirect_field_name = "redirect_to"

    def get(self, request):
        if not settings.ALLOW_VIDEO_UPLOAD and not request.user.is_staff:
            return render(request, "web/upload_video_disabled.html")
        form = VideoDetailsForm()
        return render(request, "web/upload_video.html", {"form": form})


class InboxNotifications(LoginRequiredMixin, View):
    login_url = "/signin"
    redirect_field_name = "redirect_to"

    def get(self, request):
        return render(request, "web/inbox_notifications.html")


class WatchHistoryView(LoginRequiredMixin, View):
    login_url = "/signin"
    redirect_field_name = "redirect_to"

    def get(self, request):
        categories = queries.get_all_categories()
        history = request.channel.watch_history.order_by("-created")
        all_videos = [entry.video for entry in history]
        page_number = request.GET.get("p", 1)
        paginator = Paginator(all_videos, 20)
        videos = paginator.get_page(page_number)

        return render(
            request,
            "web/watch_history.html",
            {"videos": videos, "categories": categories},
        )
