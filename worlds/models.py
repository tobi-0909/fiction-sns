from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model


class World(models.Model):
	class Visibility(models.TextChoices):
		PUBLIC = 'public', 'public'
		PRIVATE = 'private', 'private'

	title = models.CharField(max_length=120)
	description = models.TextField(blank=True)
	visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PUBLIC)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worlds')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title


class WorldMembership(models.Model):
	class Role(models.TextChoices):
		MEMBER = 'member', 'member'

	class Status(models.TextChoices):
		ACTIVE = 'active', 'active'
		KICKED = 'kicked', 'kicked'
		BANNED = 'banned', 'banned'

	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='memberships')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='world_memberships')
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
	joined_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['world', 'user'], name='unique_world_membership'),
		]
		ordering = ['world_id', 'user_id']

	def __str__(self):
		return f'{self.user} in {self.world} ({self.status})'


class WorldModerationLog(models.Model):
	class Action(models.TextChoices):
		KICK = 'kick', 'kick'
		BAN = 'ban', 'ban'

	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='moderation_logs')
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='world_moderation_actions')
	target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='world_moderation_received')
	action = models.CharField(max_length=20, choices=Action.choices)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.actor} -> {self.target_user} ({self.action}) in {self.world}'


class Character(models.Model):
	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='characters')
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='owned_characters',
	)
	name = models.CharField(max_length=120)
	profile = models.TextField(blank=True)
	personality = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.name} ({self.world.title})"


class CharacterWorldEntry(models.Model):
	"""キャラクターがWorldに登録されていることを表す中間テーブル。"""

	character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='world_entries')
	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='character_entries')
	added_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		related_name='character_entries_added',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['character', 'world'], name='unique_character_world_entry'),
		]
		ordering = ['world_id', 'character_id']

	def __str__(self):
		return f'{self.character.name} in {self.world.title}'


class Post(models.Model):
	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='posts')
	character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='posts')
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['world', '-created_at', '-id'], name='idx_post_world_timeline'),
			models.Index(fields=['author', '-created_at'], name='idx_post_author_recent'),
		]

	def clean(self):
		super().clean()
		if self.character_id and self.world_id:
			if not CharacterWorldEntry.objects.filter(
				character_id=self.character_id, world_id=self.world_id
			).exists():
				raise ValidationError({'character': '選択したCharacterはこのWorldに登録されていません。'})

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.character.name} in {self.world.title}"


class Report(models.Model):
	class TargetType(models.TextChoices):
		POST = 'post', 'post'
		USER = 'user', 'user'

	class Reason(models.TextChoices):
		SPAM = 'spam', 'spam'
		ABUSE = 'abuse', 'abuse'
		NSFW = 'nsfw', 'nsfw'
		COPYRIGHT = 'copyright', 'copyright'
		OTHER = 'other', 'other'

	class Status(models.TextChoices):
		OPEN = 'open', 'open'
		UNDER_REVIEW = 'under_review', 'under_review'
		RESOLVED = 'resolved', 'resolved'
		DISMISSED = 'dismissed', 'dismissed'

	reporter = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reports_made',
	)
	target_type = models.CharField(max_length=20, choices=TargetType.choices)
	target_post = models.ForeignKey(
		Post,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name='reports',
	)
	target_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reports_about',
	)
	reason = models.CharField(max_length=20, choices=Reason.choices)
	description = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
	created_at = models.DateTimeField(auto_now_add=True)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reports_reviewed',
	)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['status', '-created_at'], name='idx_report_status_time'),
			models.Index(fields=['reporter', '-created_at'], name='idx_report_reporter'),
		]

	def __str__(self):
		target = f'投稿 {self.target_post_id}' if self.target_post else f'ユーザー {self.target_user}'
		return f'通報: {self.reporter} -> {target} ({self.status})'
