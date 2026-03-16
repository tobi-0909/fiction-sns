from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Follow, FollowEvent


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'handle', 'display_name', 'is_private_account', 'is_staff')
    search_fields = ('email', 'handle', 'display_name', 'username')

    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('handle', 'display_name', 'bio', 'is_private_account')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('handle', 'display_name', 'email', 'is_private_account')}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'followee', 'status', 'requested_at', 'accepted_at')
    search_fields = (
        'follower__email',
        'follower__handle',
        'followee__email',
        'followee__handle',
    )
    list_filter = ('status', 'requested_at', 'accepted_at')


@admin.register(FollowEvent)
class FollowEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'action', 'actor', 'target', 'created_at')
    search_fields = (
        'actor__email',
        'actor__handle',
        'target__email',
        'target__handle',
        'actor_handle_snapshot',
        'target_handle_snapshot',
    )
    list_filter = ('action', 'created_at')
