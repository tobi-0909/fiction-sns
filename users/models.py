from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import F, Q
from django.db import models


class CustomUser(AbstractUser):
    handle = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_]+$',
                message='handleは英数字とアンダースコアのみ使用できます。',
            )
        ],
    )
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    is_private_account = models.BooleanField(default=False)


class Follow(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'pending'
        ACCEPTED = 'accepted', 'accepted'

    follower = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='following_edges',
    )
    followee = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='follower_edges',
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'followee'], name='unique_follow_edge'),
            models.CheckConstraint(
                condition=~Q(follower=F('followee')),
                name='follow_no_self_follow',
            ),
        ]
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.follower_id and self.follower_id == self.followee_id:
            raise ValidationError({'followee': '自分自身をフォローすることはできません。'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.follower} -> {self.followee} ({self.status})'


class FollowEvent(models.Model):
    class Action(models.TextChoices):
        REQUEST = 'request', 'request'
        ACCEPT = 'accept', 'accept'
        REJECT = 'reject', 'reject'
        UNFOLLOW = 'unfollow', 'unfollow'
        REMOVE_BY_BLOCK = 'remove_by_block', 'remove_by_block'

    action = models.CharField(max_length=30, choices=Action.choices)
    actor = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_events_as_actor',
    )
    target = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='follow_events_as_target',
    )
    actor_handle_snapshot = models.CharField(max_length=30, blank=True)
    target_handle_snapshot = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.actor and not self.actor_handle_snapshot:
            self.actor_handle_snapshot = self.actor.handle or self.actor.username
        if self.target and not self.target_handle_snapshot:
            self.target_handle_snapshot = self.target.handle or self.target.username
        return super().save(*args, **kwargs)

    def __str__(self):
        actor = self.actor_handle_snapshot or 'unknown'
        target = self.target_handle_snapshot or 'unknown'
        return f'{self.action}: {actor} -> {target}'


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='blocking_edges',
    )
    blocked = models.ForeignKey(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='blocked_by_edges',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['blocker', 'blocked'], name='unique_user_block'),
            models.CheckConstraint(
                condition=~Q(blocker=F('blocked')),
                name='block_no_self_block',
            ),
        ]
        ordering = ['-created_at']

    def clean(self):
        super().clean()
        if self.blocker_id and self.blocker_id == self.blocked_id:
            raise ValidationError({'blocked': '自分自身をブロックすることはできません。'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.blocker} blocks {self.blocked}'
