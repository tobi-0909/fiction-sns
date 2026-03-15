from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'email', 'handle', 'display_name', 'is_staff')
    search_fields = ('email', 'handle', 'display_name', 'username')

    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('handle', 'display_name')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('handle', 'display_name', 'email')}),
    )
