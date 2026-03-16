from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from worlds.models import Character, CharacterWorldEntry, Post, World

from .models import Follow, FollowEvent


User = get_user_model()


class PublicProfileTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='alice',
			email='alice@example.com',
			password='pass12345',
			handle='alice',
			display_name='Alice',
			bio='hello bio',
		)
		self.viewer = User.objects.create_user(
			username='bob',
			email='bob@example.com',
			password='pass12345',
			handle='bob',
			display_name='Bob',
		)

		self.world_a = World.objects.create(title='World A', owner=self.user, visibility=World.Visibility.PUBLIC)
		self.world_b = World.objects.create(title='World B', owner=self.user, visibility=World.Visibility.PUBLIC)
		self.char_a = Character.objects.create(world=self.world_a, name='Chara A', owner=self.user)
		self.char_b = Character.objects.create(world=self.world_b, name='Chara B', owner=self.user)
		CharacterWorldEntry.objects.create(character=self.char_a, world=self.world_a, added_by=self.user)
		CharacterWorldEntry.objects.create(character=self.char_b, world=self.world_b, added_by=self.user)

		Post.objects.create(world=self.world_a, character=self.char_a, author=self.user, text='post 1')
		Post.objects.create(world=self.world_a, character=self.char_a, author=self.user, text='post 2')
		Post.objects.create(world=self.world_b, character=self.char_b, author=self.user, text='post 3')

	def test_public_profile_is_accessible_by_handle_url(self):
		response = self.client.get(reverse('public_profile', args=['alice']))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '@alice')
		self.assertContains(response, 'hello bio')

	def test_profile_settings_can_update_bio(self):
		self.client.force_login(self.user)
		response = self.client.post(
			reverse('profile_settings'),
			{
				'handle': 'alice',
				'display_name': 'Alice Updated',
				'bio': 'updated bio',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.user.refresh_from_db()
		self.assertEqual(self.user.bio, 'updated bio')

	def test_public_profile_shows_activity_summary_for_self(self):
		self.client.force_login(self.user)
		response = self.client.get(reverse('public_profile', args=['alice']))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '活動サマリー')
		self.assertContains(response, '最近の投稿')
		self.assertContains(response, 'よく書くWorld')
		self.assertContains(response, 'World A')
		self.assertContains(response, '2投稿')

	def test_public_profile_hides_activity_summary_for_other_user(self):
		self.client.force_login(self.viewer)
		response = self.client.get(reverse('public_profile', args=['alice']))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '活動サマリーはフォロワー向け機能です。現在は本人のみ表示しています。')

	def test_login_page_preserves_next_in_signup_link(self):
		next_url = reverse('dashboard')
		response = self.client.get(reverse('login'), {'next': next_url})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'ログイン後、元の画面に戻ります。')
		self.assertContains(response, f'{reverse("signup")}?next={quote(next_url, safe="")}')

	def test_signup_redirects_to_login_with_next(self):
		next_url = reverse('dashboard')
		response = self.client.post(
			reverse('signup'),
			{
				'email': 'new@example.com',
				'handle': 'newuser',
				'display_name': 'New User',
				'password1': 'complex-pass-123',
				'password2': 'complex-pass-123',
				'next': next_url,
			},
		)
		self.assertRedirects(
			response,
			f'{reverse("login")}?next={next_url}',
			fetch_redirect_response=False,
		)

	def test_public_follow_button_creates_accepted_follow(self):
		self.client.force_login(self.viewer)
		response = self.client.post(
			reverse('follow_create', args=['alice']),
			{'next': reverse('public_profile', args=['alice'])},
			follow=True,
		)
		self.assertRedirects(response, reverse('public_profile', args=['alice']))
		follow = Follow.objects.get(follower=self.viewer, followee=self.user)
		self.assertEqual(follow.status, Follow.Status.ACCEPTED)
		self.assertContains(response, 'をフォローしました。')

	def test_private_follow_button_creates_pending_request(self):
		private_user = User.objects.create_user(
			username='private_owner',
			email='private@example.com',
			password='pass12345',
			handle='private_owner',
			display_name='Private Owner',
			is_private_account=True,
		)
		self.client.force_login(self.viewer)
		response = self.client.post(
			reverse('follow_create', args=['private_owner']),
			{'next': reverse('public_profile', args=['private_owner'])},
			follow=True,
		)
		self.assertRedirects(response, reverse('public_profile', args=['private_owner']))
		follow = Follow.objects.get(follower=self.viewer, followee=private_user)
		self.assertEqual(follow.status, Follow.Status.PENDING)
		self.assertContains(response, 'フォローリクエストを送りました。')

	def test_follow_action_redirects_anonymous_user_to_login(self):
		profile_url = reverse('public_profile', args=['alice'])
		response = self.client.post(
			reverse('follow_create', args=['alice']),
			{'next': profile_url},
		)
		self.assertRedirects(
			response,
			f'{reverse("login")}?next={quote(profile_url, safe="")}',
			fetch_redirect_response=False,
		)

	def test_private_account_can_accept_follow_request_from_list(self):
		private_user = User.objects.create_user(
			username='private_accept',
			email='private_accept@example.com',
			password='pass12345',
			handle='private_accept',
			display_name='Private Accept',
			is_private_account=True,
		)
		Follow.objects.create(follower=self.viewer, followee=private_user, status=Follow.Status.PENDING)
		self.client.force_login(private_user)
		list_response = self.client.get(reverse('follow_request_list'))
		self.assertContains(list_response, '@bob')
		self.assertContains(list_response, reverse('public_profile', args=['bob']))
		response = self.client.post(reverse('follow_accept', args=['bob']), follow=True)
		self.assertRedirects(response, reverse('follow_request_list'))
		follow = Follow.objects.get(follower=self.viewer, followee=private_user)
		self.assertEqual(follow.status, Follow.Status.ACCEPTED)

	def test_private_account_can_reject_follow_request(self):
		private_user = User.objects.create_user(
			username='private_reject',
			email='private_reject@example.com',
			password='pass12345',
			handle='private_reject',
			display_name='Private Reject',
			is_private_account=True,
		)
		Follow.objects.create(follower=self.viewer, followee=private_user, status=Follow.Status.PENDING)
		self.client.force_login(private_user)
		response = self.client.post(reverse('follow_reject', args=['bob']), follow=True)
		self.assertRedirects(response, reverse('follow_request_list'))
		self.assertFalse(Follow.objects.filter(follower=self.viewer, followee=private_user).exists())

	def test_following_user_can_unfollow(self):
		Follow.objects.create(follower=self.viewer, followee=self.user, status=Follow.Status.ACCEPTED)
		self.client.force_login(self.viewer)
		response = self.client.post(
			reverse('follow_delete', args=['alice']),
			{'next': reverse('public_profile', args=['alice'])},
			follow=True,
		)
		self.assertRedirects(response, reverse('public_profile', args=['alice']))
		self.assertFalse(Follow.objects.filter(follower=self.viewer, followee=self.user).exists())


class FollowModelTests(TestCase):
	def setUp(self):
		self.alice = User.objects.create_user(
			username='follow_alice',
			email='follow_alice@example.com',
			password='pass12345',
			handle='follow_alice',
		)
		self.bob = User.objects.create_user(
			username='follow_bob',
			email='follow_bob@example.com',
			password='pass12345',
			handle='follow_bob',
		)

	def test_follow_prevents_self_follow(self):
		with self.assertRaises(ValidationError):
			Follow.objects.create(follower=self.alice, followee=self.alice)

	def test_follow_prevents_duplicate_edge(self):
		Follow.objects.create(follower=self.alice, followee=self.bob)
		with self.assertRaises(ValidationError):
			Follow.objects.create(follower=self.alice, followee=self.bob)

	def test_follow_allows_refollow_after_delete(self):
		follow = Follow.objects.create(follower=self.alice, followee=self.bob)
		follow.delete()
		refollow = Follow.objects.create(follower=self.alice, followee=self.bob)
		self.assertEqual(refollow.status, Follow.Status.PENDING)

	def test_follow_event_preserves_handle_snapshots(self):
		event = FollowEvent.objects.create(
			action=FollowEvent.Action.REQUEST,
			actor=self.alice,
			target=self.bob,
		)
		self.assertEqual(event.actor_handle_snapshot, 'follow_alice')
		self.assertEqual(event.target_handle_snapshot, 'follow_bob')
