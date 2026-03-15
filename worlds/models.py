from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class World(models.Model):
	title = models.CharField(max_length=120)
	description = models.TextField(blank=True)
	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worlds')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.title


class Character(models.Model):
	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='characters')
	name = models.CharField(max_length=120)
	profile = models.TextField(blank=True)
	personality = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.name} ({self.world.title})"


class Post(models.Model):
	world = models.ForeignKey(World, on_delete=models.CASCADE, related_name='posts')
	character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='posts')
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
	text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def clean(self):
		super().clean()
		if self.character_id and self.world_id and self.character.world_id != self.world_id:
			raise ValidationError({'character': '選択したCharacterは指定Worldに属していません。'})

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.character.name} in {self.world.title}"
