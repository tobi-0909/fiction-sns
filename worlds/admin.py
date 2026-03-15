from django.contrib import admin

from .models import World


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'owner', 'created_at')
	search_fields = ('title', 'owner__email', 'owner__handle')
	list_filter = ('created_at',)
