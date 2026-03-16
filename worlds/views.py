import logging
from urllib.parse import urlencode, urlsplit

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CharacterForm, ModerationActionForm, PostForm, WorldForm
from .models import Character, CharacterWorldEntry, Post, World, WorldMembership, WorldModerationLog
from .permissions import can_post_world, can_view_world


logger = logging.getLogger(__name__)

# deny_reason classification table for issue #52.
DENY_REASON_PRIVATE_WORLD_NOT_MEMBER = 'PRIVATE_WORLD_NOT_MEMBER'
DENY_REASON_WORLD_ACTION_FORBIDDEN = 'WORLD_ACTION_FORBIDDEN'
DENY_REASON_WORLD_VIEW_FORBIDDEN = 'WORLD_VIEW_FORBIDDEN'
DENY_REASON_UNKNOWN = 'UNKNOWN'

EXPECTED_DENY_REASONS = {
	DENY_REASON_PRIVATE_WORLD_NOT_MEMBER,
	DENY_REASON_WORLD_ACTION_FORBIDDEN,
	DENY_REASON_WORLD_VIEW_FORBIDDEN,
}

DENY_REASON_MESSAGES = {
	DENY_REASON_PRIVATE_WORLD_NOT_MEMBER: 'このWorldは非公開です。参加には作成者の承認が必要です。',
	DENY_REASON_WORLD_ACTION_FORBIDDEN: 'このWorldで操作する権限がありません。',
	DENY_REASON_WORLD_VIEW_FORBIDDEN: 'このWorldを閲覧する権限がありません。',
	DENY_REASON_UNKNOWN: '不明な理由でアクセスが拒否されました。時間をおいて再試行してください。',
}


def _is_async_request(request):
	accept = request.headers.get('Accept', '')
	return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in accept


def _build_auth_url(view_name, next_url=''):
	url = reverse(view_name)
	if next_url:
		return f"{url}?{urlencode({'next': next_url})}"
	return url


def _get_login_next_url(request):
	if request.method == 'POST':
		referer = request.META.get('HTTP_REFERER', '')
		if referer:
			parsed = urlsplit(referer)
			if not parsed.netloc or parsed.netloc == request.get_host():
				path = parsed.path or '/'
				if parsed.query:
					return f'{path}?{parsed.query}'
				return path
	return request.get_full_path()


def _redirect_to_login(request, message):
	messages.warning(request, message)
	return redirect(_build_auth_url('login', _get_login_next_url(request)))


def _deny_world_access(request, deny_reason):
	message = DENY_REASON_MESSAGES.get(deny_reason, DENY_REASON_MESSAGES[DENY_REASON_UNKNOWN])
	user_id = request.user.id if request.user.is_authenticated else None
	logger.info('World access denied: reason=%s user_id=%s path=%s', deny_reason, user_id, request.path)

	if _is_async_request(request):
		return JsonResponse({'ok': False, 'deny_reason': deny_reason, 'message': message}, status=403)

	if deny_reason in EXPECTED_DENY_REASONS:
		if not request.user.is_authenticated:
			return _redirect_to_login(request, 'ログインすると続きから確認できます。')
		messages.warning(request, message)
		return redirect('world_list')

	return render(request, 'worlds/access_denied.html', {'message': message}, status=403)


@login_required
def world_list(request):
	worlds = World.objects.filter(owner=request.user)
	return render(request, 'worlds/world_list.html', {'worlds': worlds})


@login_required
def world_create(request):
	if request.method == 'POST':
		form = WorldForm(request.POST)
		if form.is_valid():
			world = form.save(commit=False)
			world.owner = request.user
			world.save()
			return redirect('world_list')
	else:
		form = WorldForm()

	return render(request, 'worlds/world_form.html', {'form': form, 'mode': 'create'})


def world_timeline(request, world_id):
	world = get_object_or_404(World, id=world_id)
	if not can_view_world(request.user, world):
		if world.visibility == World.Visibility.PRIVATE:
			return _deny_world_access(request, DENY_REASON_PRIVATE_WORLD_NOT_MEMBER)
		return _deny_world_access(request, DENY_REASON_WORLD_VIEW_FORBIDDEN)
	posts = Post.objects.filter(world=world).select_related('character', 'author')
	post_create_url = reverse('post_create', args=[world.id])
	return render(
		request,
		'worlds/world_timeline.html',
		{
			'world': world,
			'posts': posts,
			'can_post': can_post_world(request.user, world),
			'login_to_post_url': _build_auth_url('login', post_create_url),
			'signup_to_post_url': _build_auth_url('signup', post_create_url),
		},
	)


@login_required
def post_create(request, world_id):
	world = get_object_or_404(World, id=world_id)
	if not can_post_world(request.user, world):
		return _deny_world_access(request, DENY_REASON_WORLD_ACTION_FORBIDDEN)

	if request.method == 'POST':
		form = PostForm(request.POST, world=world, user=request.user)
		if form.is_valid():
			post = form.save(commit=False)
			post.world = world
			post.author = request.user
			post.save()
			messages.success(request, '投稿を作成しました。')
			return redirect('world_timeline', world_id=world.id)
	else:
		form = PostForm(world=world, user=request.user)

	return render(request, 'worlds/post_form.html', {'form': form, 'world': world})


@login_required
def world_edit(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		form = WorldForm(request.POST, instance=world)
		if form.is_valid():
			form.save()
			return redirect('world_list')
	else:
		form = WorldForm(instance=world)

	return render(request, 'worlds/world_form.html', {'form': form, 'mode': 'edit', 'world': world})


@login_required
def world_delete(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		world.delete()
		return redirect('world_list')

	return render(request, 'worlds/world_confirm_delete.html', {'world': world})


@login_required
def world_moderation(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		form = ModerationActionForm(request.POST, world=world, actor=request.user)
		if form.is_valid():
			target_user = form.target_user
			action = form.cleaned_data['action']
			membership = WorldMembership.objects.filter(world=world, user=target_user).first()

			if action == ModerationActionForm.ACTION_KICK:
				membership.status = WorldMembership.Status.KICKED
				membership.save(update_fields=['status', 'updated_at'])
				WorldModerationLog.objects.create(
					world=world,
					actor=request.user,
					target_user=target_user,
					action=WorldModerationLog.Action.KICK,
				)
				messages.success(request, f'@{target_user.handle or target_user.username} を kick しました。')
			else:
				membership, _ = WorldMembership.objects.get_or_create(
					world=world,
					user=target_user,
					defaults={'status': WorldMembership.Status.BANNED},
				)
				if membership.status != WorldMembership.Status.BANNED:
					membership.status = WorldMembership.Status.BANNED
					membership.save(update_fields=['status', 'updated_at'])
				WorldModerationLog.objects.create(
					world=world,
					actor=request.user,
					target_user=target_user,
					action=WorldModerationLog.Action.BAN,
				)
				messages.success(request, f'@{target_user.handle or target_user.username} を ban しました。')

			return redirect('world_moderation', world_id=world.id)
	else:
		form = ModerationActionForm(world=world, actor=request.user)

	memberships = WorldMembership.objects.filter(world=world).select_related('user')
	logs = WorldModerationLog.objects.filter(world=world).select_related('actor', 'target_user')[:20]
	return render(
		request,
		'worlds/world_moderation.html',
		{'world': world, 'form': form, 'memberships': memberships, 'logs': logs},
	)


@login_required
def character_list(request, world_id):
	world = get_object_or_404(World, id=world_id)
	if not can_post_world(request.user, world):
		return _deny_world_access(request, DENY_REASON_WORLD_ACTION_FORBIDDEN)
	entries = (
		CharacterWorldEntry.objects
		.filter(world=world)
		.select_related('character', 'character__owner', 'character__world')
		.order_by('created_at')
	)
	return render(request, 'worlds/character_list.html', {'world': world, 'entries': entries})


@login_required
def character_create(request, world_id):
	world = get_object_or_404(World, id=world_id)
	if not can_post_world(request.user, world):
		return _deny_world_access(request, DENY_REASON_WORLD_ACTION_FORBIDDEN)

	if request.method == 'POST':
		form = CharacterForm(request.POST)
		if form.is_valid():
			character = form.save(commit=False)
			character.world = world
			character.owner = request.user
			character.save()
			CharacterWorldEntry.objects.create(character=character, world=world, added_by=request.user)
			return redirect('character_list', world_id=world.id)
	else:
		form = CharacterForm()

	return render(request, 'worlds/character_form.html', {'form': form, 'mode': 'create', 'world': world})


@login_required
def character_edit(request, world_id, character_id):
	world = get_object_or_404(World, id=world_id)
	character = get_object_or_404(Character, id=character_id)
	# character がこの World に存在することを確認（home 作成 + 持ち込みどちらも CharacterWorldEntry で統一）
	get_object_or_404(CharacterWorldEntry, character=character, world=world)
	if character.owner != request.user:
		messages.warning(request, 'このキャラクターを編集する権限がありません。')
		return redirect('character_list', world_id=world.id)

	if request.method == 'POST':
		form = CharacterForm(request.POST, instance=character)
		if form.is_valid():
			form.save()
			return redirect('character_list', world_id=world.id)
	else:
		form = CharacterForm(instance=character)

	return render(
		request,
		'worlds/character_form.html',
		{'form': form, 'mode': 'edit', 'world': world, 'character': character},
	)


@login_required
def character_delete(request, world_id, character_id):
	world = get_object_or_404(World, id=world_id)
	character = get_object_or_404(Character, id=character_id)
	# character がこの World に存在することを確認
	get_object_or_404(CharacterWorldEntry, character=character, world=world)
	if character.owner != request.user:
		messages.warning(request, 'このキャラクターを削除する権限がありません。')
		return redirect('character_list', world_id=world.id)

	if request.method == 'POST':
		character.delete()
		return redirect('character_list', world_id=world.id)

	return render(request, 'worlds/character_confirm_delete.html', {'world': world, 'character': character})


@login_required
def character_bring_in(request, world_id):
	"""自分のCharacterを他人のWorldに持ち込む。"""
	world = get_object_or_404(World, id=world_id)
	if not can_post_world(request.user, world):
		return _deny_world_access(request, DENY_REASON_WORLD_ACTION_FORBIDDEN)

	already_in_ids = set(
		CharacterWorldEntry.objects.filter(world=world).values_list('character_id', flat=True)
	)
	available = Character.objects.filter(owner=request.user).exclude(id__in=already_in_ids)

	if request.method == 'POST':
		character_id = request.POST.get('character_id')
		character = get_object_or_404(Character, id=character_id, owner=request.user)
		if character.id in already_in_ids:
			messages.warning(request, 'このキャラクターはすでにこのWorldに追加されています。')
		else:
			CharacterWorldEntry.objects.create(character=character, world=world, added_by=request.user)
			# PUBLIC World への初回持ち込み時に WorldMembership を auto-create する。
			# これにより、以後の kick/ban 管理が適用できるようになる。
			if world.visibility == World.Visibility.PUBLIC and world.owner_id != request.user.id:
				WorldMembership.objects.get_or_create(
					world=world,
					user=request.user,
					defaults={'status': WorldMembership.Status.ACTIVE},
				)
			messages.success(request, f'{character.name} をこのWorldに追加しました。')
		return redirect('character_list', world_id=world.id)

	return render(
		request,
		'worlds/character_bring_in.html',
		{'world': world, 'available_characters': available},
	)
