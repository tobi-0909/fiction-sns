from django.contrib import admin

from .models import Character, Post, World


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


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
	list_display = ('id', 'world', 'character', 'author', 'created_at')
	search_fields = ('world__title', 'character__name', 'author__email', 'author__handle', 'text')
	list_filter = ('created_at', 'world', 'character')
