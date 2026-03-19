from urllib.parse import urlencode

from django.contrib import messages
from django.db import models
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotAllowed
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from django.contrib.auth import get_user_model

from worlds.models import Post, WorldMembership

from .models import Follow, FollowEvent, UserBlock
from .forms import (
	CustomUserCreationForm,
	EmailOrHandleAuthenticationForm,
	ProfileSettingsForm,
)


User = get_user_model()


def _get_safe_next_url(request):
	next_url = request.POST.get('next') or request.GET.get('next') or ''
	if next_url and url_has_allowed_host_and_scheme(
		next_url,
		allowed_hosts={request.get_host()},
		require_https=request.is_secure(),
	):
		return next_url
	return ''


def _build_auth_url(view_name, next_url=''):
	url = reverse(view_name)
	if next_url:
		return f"{url}?{urlencode({'next': next_url})}"
	return url


def _resolve_user_by_handle(handle):
	normalized_handle = handle.strip().lstrip('@').lower()
	return get_object_or_404(User, handle__iexact=normalized_handle)


def _redirect_to_login(request, next_url):
	messages.warning(request, 'この操作にはログインが必要です。')
	return redirect(_build_auth_url('login', next_url))


def _record_follow_event(action, actor, target):
	FollowEvent.objects.create(action=action, actor=actor, target=target)


def _accepted_follow(viewer, profile_user):
	if not viewer.is_authenticated:
		return False
	return Follow.objects.filter(
		follower=viewer,
		followee=profile_user,
		status=Follow.Status.ACCEPTED,
	).exists()


def _find_block_reason(viewer, profile_user):
	if not viewer.is_authenticated:
		return ''
	if UserBlock.objects.filter(blocker=profile_user, blocked=viewer).exists():
		return 'このユーザーにブロックされているためフォローできません。'
	if UserBlock.objects.filter(blocker=viewer, blocked=profile_user).exists():
		return 'ブロック中のユーザーはフォローできません。'
	return ''


def _is_banned_by_profile_owner(viewer, profile_user):
	if not viewer.is_authenticated:
		return False
	return WorldMembership.objects.filter(
		world__owner=profile_user,
		user=viewer,
		status=WorldMembership.Status.BANNED,
	).exists()


def _can_view_private_profile_details(viewer, profile_user, is_self):
	if not profile_user.is_private_account:
		return True
	if is_self:
		return True
	return _accepted_follow(viewer, profile_user)


def _remove_follow_relation(follower, followee, actor):
	follow = Follow.objects.filter(follower=follower, followee=followee).first()
	if not follow:
		return False
	follow.delete()
	_record_follow_event(FollowEvent.Action.REMOVE_BY_BLOCK, actor, follower)
	return True


def _accept_pending_requests_for_public_profile(user):
	pending_follows = list(
		Follow.objects.filter(
			followee=user,
			status=Follow.Status.PENDING,
		).select_related('follower')
	)
	accepted_count = 0
	for follow in pending_follows:
		follow.status = Follow.Status.ACCEPTED
		follow.accepted_at = timezone.now()
		follow.save(update_fields=['status', 'accepted_at', 'updated_at'])
		_record_follow_event(FollowEvent.Action.ACCEPT, user, follow.follower)
		accepted_count += 1
	return accepted_count


class CustomLoginView(LoginView):
	template_name = 'registration/login.html'
	authentication_form = EmailOrHandleAuthenticationForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		next_url = _get_safe_next_url(self.request)
		context['next_url'] = next_url
		context['signup_url'] = _build_auth_url('signup', next_url)
		return context


def signup(request):
	next_url = _get_safe_next_url(request)
	if request.user.is_authenticated:
		return redirect(next_url or 'dashboard')

	if request.method == 'POST':
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect(_build_auth_url('login', next_url))
	else:
		form = CustomUserCreationForm()

	return render(
		request,
		'users/signup.html',
		{
			'form': form,
			'next_url': next_url,
			'login_url': _build_auth_url('login', next_url),
		},
	)


@login_required
def dashboard(request):
	return render(request, 'users/dashboard.html')


@login_required
def profile_settings(request):
	if request.method == 'POST':
		was_private = request.user.is_private_account
		form = ProfileSettingsForm(request.POST, instance=request.user)
		if form.is_valid():
			updated_user = form.save()
			if was_private and not updated_user.is_private_account:
				accepted_count = _accept_pending_requests_for_public_profile(updated_user)
				if accepted_count:
					messages.info(request, f'公開アカウントへの変更により、{accepted_count} 件のフォローリクエストを承認しました。')
			return redirect('dashboard')
	else:
		form = ProfileSettingsForm(instance=request.user)

	return render(request, 'users/profile_settings.html', {'form': form})


def follow_create(request, handle):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	profile_user = _resolve_user_by_handle(handle)
	next_url = _get_safe_next_url(request) or reverse('public_profile', args=[profile_user.handle])
	if not request.user.is_authenticated:
		return _redirect_to_login(request, next_url)
	if request.user.pk == profile_user.pk:
		messages.warning(request, '自分自身をフォローすることはできません。')
		return redirect(next_url)

	block_reason = _find_block_reason(request.user, profile_user)
	if block_reason:
		_remove_follow_relation(request.user, profile_user, profile_user)
		messages.warning(request, block_reason)
		return redirect(next_url)

	if _is_banned_by_profile_owner(request.user, profile_user):
		_remove_follow_relation(request.user, profile_user, profile_user)
		messages.warning(request, 'このユーザーが管理するWorldでBAN状態のためフォローできません。')
		return redirect(next_url)

	defaults = {'status': Follow.Status.PENDING}
	if not profile_user.is_private_account:
		defaults['status'] = Follow.Status.ACCEPTED
		defaults['accepted_at'] = timezone.now()

	follow, created = Follow.objects.get_or_create(
		follower=request.user,
		followee=profile_user,
		defaults=defaults,
	)

	if created:
		_record_follow_event(FollowEvent.Action.REQUEST, request.user, profile_user)
		if follow.status == Follow.Status.ACCEPTED:
			_record_follow_event(FollowEvent.Action.ACCEPT, profile_user, request.user)
			messages.success(request, f'@{profile_user.handle} をフォローしました。')
		else:
			messages.success(request, f'@{profile_user.handle} にフォローリクエストを送りました。')
		return redirect(next_url)

	if profile_user.is_private_account and follow.status == Follow.Status.PENDING:
		messages.info(request, 'このユーザーにはすでにフォローリクエストを送信済みです。')
		return redirect(next_url)

	if not profile_user.is_private_account and follow.status == Follow.Status.PENDING:
		follow.status = Follow.Status.ACCEPTED
		follow.accepted_at = timezone.now()
		follow.save(update_fields=['status', 'accepted_at', 'updated_at'])
		_record_follow_event(FollowEvent.Action.ACCEPT, profile_user, request.user)
		messages.success(request, f'@{profile_user.handle} をフォローしました。')
		return redirect(next_url)

	messages.info(request, f'@{profile_user.handle} はすでにフォロー中です。')
	return redirect(next_url)


def follow_delete(request, handle):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	profile_user = _resolve_user_by_handle(handle)
	next_url = _get_safe_next_url(request) or reverse('public_profile', args=[profile_user.handle])
	if not request.user.is_authenticated:
		return _redirect_to_login(request, next_url)

	follow = Follow.objects.filter(follower=request.user, followee=profile_user).first()
	if not follow:
		messages.info(request, 'フォロー関係は存在しません。')
		return redirect(next_url)

	follow.delete()
	_record_follow_event(FollowEvent.Action.UNFOLLOW, request.user, profile_user)
	messages.success(request, f'@{profile_user.handle} のフォローを解除しました。')
	return redirect(next_url)


@login_required
def follow_request_list(request):
	pending_requests = (
		Follow.objects.filter(followee=request.user, status=Follow.Status.PENDING)
		.select_related('follower')
		.order_by('requested_at')
	)
	return render(
		request,
		'users/follow_request_list.html',
		{
			'pending_requests': pending_requests,
		},
	)


@login_required
def follow_accept(request, handle):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	requester = _resolve_user_by_handle(handle)
	follow = get_object_or_404(
		Follow,
		follower=requester,
		followee=request.user,
		status=Follow.Status.PENDING,
	)
	follow.status = Follow.Status.ACCEPTED
	follow.accepted_at = timezone.now()
	follow.save(update_fields=['status', 'accepted_at', 'updated_at'])
	_record_follow_event(FollowEvent.Action.ACCEPT, request.user, requester)
	messages.success(request, f'@{requester.handle} のフォローリクエストを承認しました。')
	return redirect('follow_request_list')


@login_required
def follow_reject(request, handle):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	requester = _resolve_user_by_handle(handle)
	follow = get_object_or_404(
		Follow,
		follower=requester,
		followee=request.user,
		status=Follow.Status.PENDING,
	)
	follow.delete()
	_record_follow_event(FollowEvent.Action.REJECT, request.user, requester)
	messages.success(request, f'@{requester.handle} のフォローリクエストを拒否しました。')
	return redirect('follow_request_list')


def following_list(request, handle):
	profile_user = _resolve_user_by_handle(handle)
	is_self = request.user.is_authenticated and request.user.pk == profile_user.pk
	if profile_user.is_private_account and not _can_view_private_profile_details(request.user, profile_user, is_self):
		if not request.user.is_authenticated:
			return _redirect_to_login(request, reverse('following_list', args=[profile_user.handle]))
		messages.warning(request, '鍵アカウントのフォロー一覧はフォロワーのみ閲覧できます。')
		return redirect('public_profile', handle=profile_user.handle)

	following_edges = (
		Follow.objects.filter(
			follower=profile_user,
			status=Follow.Status.ACCEPTED,
		)
		.select_related('followee')
		.order_by('-accepted_at', '-created_at')
	)
	paginator = Paginator(following_edges, 20)
	page_obj = paginator.get_page(request.GET.get('page'))
	return render(
		request,
		'users/follow_list.html',
		{
			'profile_user': profile_user,
			'page_obj': page_obj,
			'list_type': 'following',
			'title': 'フォロー中',
			'empty_message': 'まだ誰もフォローしていません。',
		},
	)


def follower_list(request, handle):
	profile_user = _resolve_user_by_handle(handle)
	is_self = request.user.is_authenticated and request.user.pk == profile_user.pk
	if profile_user.is_private_account and not _can_view_private_profile_details(request.user, profile_user, is_self):
		if not request.user.is_authenticated:
			return _redirect_to_login(request, reverse('follower_list', args=[profile_user.handle]))
		messages.warning(request, '鍵アカウントのフォロワー一覧はフォロワーのみ閲覧できます。')
		return redirect('public_profile', handle=profile_user.handle)

	follower_edges = (
		Follow.objects.filter(
			followee=profile_user,
			status=Follow.Status.ACCEPTED,
		)
		.select_related('follower')
		.order_by('-accepted_at', '-created_at')
	)
	paginator = Paginator(follower_edges, 20)
	page_obj = paginator.get_page(request.GET.get('page'))
	return render(
		request,
		'users/follow_list.html',
		{
			'profile_user': profile_user,
			'page_obj': page_obj,
			'list_type': 'followers',
			'title': 'フォロワー',
			'empty_message': 'まだフォロワーはいません。',
		},
	)


def public_profile(request, handle):
	profile_user = _resolve_user_by_handle(handle)

	is_self = request.user.is_authenticated and request.user.pk == profile_user.pk
	viewer_follow = None
	viewer_block = None
	follow_action_blocked_reason = ''
	if request.user.is_authenticated and not is_self:
		viewer_follow = Follow.objects.filter(follower=request.user, followee=profile_user).first()
		viewer_block = UserBlock.objects.filter(blocker=request.user, blocked=profile_user).first()
		follow_action_blocked_reason = _find_block_reason(request.user, profile_user)
		if not follow_action_blocked_reason and _is_banned_by_profile_owner(request.user, profile_user):
			follow_action_blocked_reason = 'このユーザーが管理するWorldでBAN状態のためフォローできません。'

	can_view_profile_details = _can_view_private_profile_details(request.user, profile_user, is_self)
	can_view_activity_summary = can_view_profile_details and (is_self or _accepted_follow(request.user, profile_user))
	recent_posts = []
	top_worlds = []
	following_count = Follow.objects.filter(follower=profile_user, status=Follow.Status.ACCEPTED).count()
	follower_count = Follow.objects.filter(followee=profile_user, status=Follow.Status.ACCEPTED).count()
	pending_request_count = 0
	if is_self:
		pending_request_count = Follow.objects.filter(
			followee=profile_user,
			status=Follow.Status.PENDING,
		).count()

	if can_view_activity_summary:
		recent_posts = list(
			Post.objects.filter(author=profile_user)
			.select_related('world', 'character')
			.order_by('-created_at')[:5]
		)

		top_worlds = list(
			Post.objects.filter(author=profile_user)
			.values('world_id', 'world__title')
			.annotate(post_count=Count('id'))
			.order_by('-post_count', 'world__title')[:5]
		)

	return render(
		request,
		'users/public_profile.html',
		{
			'profile_user': profile_user,
			'is_self': is_self,
			'viewer_follow': viewer_follow,
			'viewer_block': viewer_block,
			'can_view_profile_details': can_view_profile_details,
			'follow_action_blocked_reason': follow_action_blocked_reason,
			'can_view_activity_summary': can_view_activity_summary,
			'recent_posts': recent_posts,
			'top_worlds': top_worlds,
			'following_count': following_count,
			'follower_count': follower_count,
			'pending_request_count': pending_request_count,
		},
	)


@login_required
def block_user(request, user_id):
	"""ユーザーをブロックする。"""
	target_user = get_object_or_404(User, id=user_id)
	
	if target_user.id == request.user.id:
		messages.warning(request, '自分自身はブロックできません。')
		return redirect('public_profile', handle=target_user.handle)
	
	if request.method == 'POST':
		UserBlock.objects.get_or_create(blocker=request.user, blocked=target_user)
		
		# ブロック時に既存のフォロー関係を削除する
		Follow.objects.filter(
			models.Q(follower=request.user, followee=target_user) |
			models.Q(follower=target_user, followee=request.user)
		).delete()
		
		messages.success(request, f'{target_user.handle or target_user.username} をブロックしました。')
		return redirect('public_profile', handle=target_user.handle)
	
	return redirect('public_profile', handle=target_user.handle)


@login_required
def unblock_user(request, user_id):
	"""ユーザーのブロックを解除する。"""
	target_user = get_object_or_404(User, id=user_id)
	
	if request.method == 'POST':
		UserBlock.objects.filter(blocker=request.user, blocked=target_user).delete()
		messages.success(request, f'{target_user.handle or target_user.username} のブロックを解除しました。')
		return redirect('public_profile', handle=target_user.handle)
	
	return redirect('public_profile', handle=target_user.handle)
