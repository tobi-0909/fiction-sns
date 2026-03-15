from django.contrib import admin

from .models import Character, World


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'owner', 'created_at')
	search_fields = ('title', 'owner__email', 'owner__handle')
	list_filter = ('created_at',)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'world', 'created_at')
	search_fields = ('name', 'world__title', 'world__owner__email', 'world__owner__handle')
	list_filter = ('created_at', 'world')
