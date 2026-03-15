from django.conf import settings
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
