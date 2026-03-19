from django.contrib import admin

from .models import Character, Post, World, WorldMembership, WorldModerationLog, Report


@admin.register(World)
class WorldAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'visibility', 'owner', 'created_at')
	search_fields = ('title', 'owner__email', 'owner__handle')
	list_filter = ('visibility', 'created_at')


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


@admin.register(WorldMembership)
class WorldMembershipAdmin(admin.ModelAdmin):
	list_display = ('id', 'world', 'user', 'role', 'status', 'joined_at', 'updated_at')
	search_fields = ('world__title', 'user__email', 'user__handle')
	list_filter = ('role', 'status', 'world')


@admin.register(WorldModerationLog)
class WorldModerationLogAdmin(admin.ModelAdmin):
	list_display = ('id', 'world', 'actor', 'target_user', 'action', 'created_at')
	search_fields = ('world__title', 'actor__email', 'actor__handle', 'target_user__email', 'target_user__handle')
	list_filter = ('action', 'world', 'created_at')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
	list_display = ('id', 'target_type', 'reporter', 'status', 'reason', 'created_at')
	search_fields = (
		'reporter__email',
		'reporter__handle',
		'target_user__email',
		'target_user__handle',
		'target_post__id',
		'description',
	)
	list_filter = ('status', 'reason', 'target_type', 'created_at')
	readonly_fields = ('created_at', 'reviewed_at')
	fieldsets = (
		('通報内容', {
			'fields': ('reporter', 'target_type', 'target_post', 'target_user', 'reason', 'description'),
		}),
		('レビュー', {
			'fields': ('status', 'reviewed_by', 'created_at', 'reviewed_at'),
		}),
	)
