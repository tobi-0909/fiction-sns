from urllib.parse import urlencode

from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotAllowed
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from django.contrib.auth import get_user_model

from worlds.models import Post

from .models import Follow, FollowEvent
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
		form = ProfileSettingsForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
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


def public_profile(request, handle):
	profile_user = _resolve_user_by_handle(handle)

	is_self = request.user.is_authenticated and request.user.pk == profile_user.pk
	viewer_follow = None
	if request.user.is_authenticated and not is_self:
		viewer_follow = Follow.objects.filter(follower=request.user, followee=profile_user).first()
	can_view_activity_summary = is_self or _accepted_follow(request.user, profile_user)
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
			'can_view_activity_summary': can_view_activity_summary,
			'recent_posts': recent_posts,
			'top_worlds': top_worlds,
			'following_count': following_count,
			'follower_count': follower_count,
			'pending_request_count': pending_request_count,
		},
	)
