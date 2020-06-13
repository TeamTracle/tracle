from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import Channel, Video, Category

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

    list_display = ('email', 'admin')
    list_filter = ('admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('active', 'admin', 'staff')}),
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
    fields = ('watch_id', 'thumbnail', 'title', 'description', 'visibility', 'views', 'created', 'uploaded_file', 'job_id', 'category', 'channel')

admin.site.register(User, UserAdmin)
admin.site.register(Channel)
admin.site.register(Category)
admin.site.register(Video)
