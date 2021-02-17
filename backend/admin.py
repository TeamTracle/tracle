from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry
from django.forms import ModelForm
from django.utils.html import format_html

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Channel, Video, Category, Comment, CommentTicket, VideoTicket, VideoStrike

User = get_user_model()

class ChannelsInline(admin.TabularInline):
    model = Channel
    can_delete = False
    show_change_link = True
    readonly_fields = ('name', 'show_url')
    fieldsets = (
        (None, {'fields': ('name', 'show_url')}),
    )

    def show_url(self, obj):
        url = f'/channel/{obj.channel_id}'
        return  format_html('<a href="{}">{}</a>', url, url)

    show_url.short_description = 'URL'

    extra = 0
    max_num = 0

class VideoStrikesInline(admin.TabularInline):
    model = VideoStrike
    can_delete = False
    show_change_link = False
    extra = 0
    max_num = 1
    readonly_fields = ['created']
    fields = ['channel', 'video', 'category', 'created']

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super(VideoStrikesInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'channel':
            if self.parent_obj and isinstance(self.parent_obj, Video):
                kwargs['queryset'] = Channel.objects.filter(pk=self.parent_obj.channel_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = ('email', 'is_superuser', 'banned')
    list_filter = ('is_superuser', 'banned')
    readonly_fields = ('ipadress', 'banned', 'banned_at', 'is_superuser', 'staff', 'email')
    fieldsets = (
        (None, {'fields': ('email', 'notes', 'ipadress')}),
        ('Permissions', {'fields': ('is_superuser', 'staff', 'banned', 'banned_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    inlines = [ChannelsInline]

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'watch_id', 'created', 'transcode_status')
    list_filter = ('transcode_status',)
    search_fields = ('title', 'watch_id')
    ordering = ('title', 'created')

    readonly_fields = ('title_with_link', 'description', 'visibility', 'transcode_status', 'uploaded_file', 'playlist_file', 'views', 'created', 'category', 'channel_with_link')
    fieldsets = (
        (None, {'fields': ('title_with_link', 'description', 'visibility', 'views', 'created', 'channel_with_link', 'category')}),
        (None, {'fields': ('transcode_status', 'uploaded_file', 'playlist_file')}),
    )

    inlines = [VideoStrikesInline]

    def title_with_link(self, obj):
        url = f'/watch?v={obj.watch_id}'
        return format_html('{} <a href="{}">View on site</a>', obj.title, url)
    title_with_link.short_description = 'Title'

    def channel_with_link(self, obj):
        url = f'/channel/{obj.channel.channel_id}'
        return format_html('{} <a href="{}">View on site</a>', obj.channel.name, url)
    channel_with_link.short_description = 'Created by'

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            yield inline.get_formset(request, obj), inline

class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('name', 'view_channel_on_site', 'description', 'created', 'last_login', 'avatar', 'verified', 'user', 'show_url')
    fields = ('name', 'view_channel_on_site', 'description', 'created', 'last_login', 'avatar', 'verified', ('user', 'show_url'))

    inlines = [VideoStrikesInline]

    def show_url(self, obj):
        url = f'/admin/backend/user/{obj.user.pk}'
        return format_html('<a href="{}">{}</a>', url, url)
    show_url.short_description = 'Change:'

    def view_channel_on_site(self, obj):
        url = f'/channel/{obj.channel_id}'
        return format_html('<a href="{}">{}</a>', url, url)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            inline.readonly_fields = inline.fields
            yield inline.get_formset(request, obj), inline

class TicketAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'created')
    ordering = ('created',)
    list_filter = ('status',)

class CommentTicketAdmin(TicketAdmin):
    readonly_fields = ('reason', 'reporter', 'reported_comment', 'body', 'created')
    fields = ('status', 'reporter', 'reason', 'reported_comment', 'body', 'created')

    def reporter(self, obj):
        url = f'/admin/backend/channel/{obj.channel.pk}'
        name = obj.channel.name
        return format_html('<a href="{}">{}</a>', url, name)

    def reported_comment(self, obj):
        url = f'/admin/backend/comment/{obj.comment.pk}'
        name = str(obj.comment)
        return format_html('<a href="{}">{}</a>', url, name)

class VideoTicketAdmin(TicketAdmin):
    readonly_fields = ('reason', 'reporter', 'reported_video', 'body', 'created')
    fields = ('status', 'reporter', 'reason', 'reported_video', 'body', 'created')

    def reporter(self, obj):
        url = f'/admin/backend/channel/{obj.channel.pk}'
        name = obj.channel.name
        return format_html('<a href="{}">{}</a>', url, name)

    def reported_video(self, obj):
        url = f'/admin/backend/video/{obj.video.pk}'
        name = obj.video.title
        return format_html('<a href="{}">{}</a>', url, name)

class LogAdmin(admin.ModelAdmin):
    list_display = ('user', '__str__', 'action_time')
    search_fields = ('user', '__str__')

class CommentAdmin(admin.ModelAdmin):
    readonly_fields = ('author', 'video_title', 'text', 'created', 'show_url', 'author_url')
    fields = (('author', 'author_url'), 'video_title', 'text', 'created', 'show_url')

    def video_title(self, obj):
        return obj.video.title
    video_title.short_description = 'Video'

    def show_url(self, obj):
        url = f'/watch?v={obj.video.watch_id}#comment-{obj.pk}'
        return format_html('<a href="{}">{}</a>', url, url)
    show_url.short_description = 'View on site'

    def author_url(self, obj):
        url = f'/admin/backend/channel/{obj.author.pk}'
        return format_html('<a href="{}">{}</a>', url, url)
    author_url.short_description = 'View'

admin.site.register(User, UserAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentTicket, CommentTicketAdmin)
admin.site.register(VideoTicket, VideoTicketAdmin)
admin.site.register(LogEntry, LogAdmin)
