from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.models import LogEntry

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Channel, Video, Category, Comment, CommentTicket, VideoTicket

User = get_user_model()

class ChannelsInline(admin.TabularInline):
    model = Channel
    fieldsets = (
        (None, {'fields': ('name',)}),
    )
    extra = 0

class UserAdmin(BaseUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    list_display = ('email', 'is_superuser', 'banned')
    list_filter = ('is_superuser', 'banned')
    readonly_fields = ('ipadress', 'banned', 'banned_at', 'is_superuser', 'staff')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'notes', 'ipadress')}),
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
    fields = ('watch_id', 'title', 'description', 'visibility', 'views', 'created', 'uploaded_file', 'job_id', 'category', 'channel')

class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class TicketAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'created')
    ordering = ('created',)
    list_filter = ('status',)


class LogAdmin(admin.ModelAdmin):
    list_display = ('user', '__str__', 'action_time')
    search_fields = ('user', '__str__')

admin.site.register(User, UserAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Category)
admin.site.register(Video)
admin.site.register(Comment)
admin.site.register(CommentTicket, TicketAdmin)
admin.site.register(VideoTicket, TicketAdmin)
admin.site.register(LogEntry, LogAdmin)
