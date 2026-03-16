from __future__ import annotations

from .models import World, WorldMembership


def _get_membership(world: World, user):
	if not user.is_authenticated:
		return None
	return WorldMembership.objects.filter(world=world, user=user).first()


def can_view_world(user, world: World) -> bool:
	if not user.is_authenticated:
		return world.visibility == World.Visibility.PUBLIC

	if world.owner_id == user.id:
		return True

	membership = _get_membership(world, user)

	if world.visibility == World.Visibility.PUBLIC:
		return True

	return membership is not None and membership.status == WorldMembership.Status.ACTIVE


def can_post_world(user, world: World) -> bool:
	if not user.is_authenticated:
		return False

	if world.owner_id == user.id:
		return True

	membership = _get_membership(world, user)

	# PUBLIC worlds: blocked only if explicitly kicked or banned.
	# Users with no membership record are treated as allowed participants.
	if world.visibility == World.Visibility.PUBLIC:
		if membership is None:
			return True
		return membership.status == WorldMembership.Status.ACTIVE

	# PRIVATE worlds: require active membership.
	if membership is None:
		return False
	return membership.status == WorldMembership.Status.ACTIVE
