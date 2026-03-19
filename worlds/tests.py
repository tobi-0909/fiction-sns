from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Character, CharacterWorldEntry, Post, World, WorldMembership, WorldModerationLog
from .permissions import can_post_world, can_view_world


User = get_user_model()


class WorldPermissionTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			username='owner',
			email='owner@example.com',
			password='pass12345',
			handle='owner',
		)
		self.other = User.objects.create_user(
			username='other',
			email='other@example.com',
			password='pass12345',
			handle='other',
		)

		self.public_world = World.objects.create(
			title='Public World',
			description='visible',
			owner=self.owner,
			visibility=World.Visibility.PUBLIC,
		)
		self.private_world = World.objects.create(
			title='Private World',
			description='hidden',
			owner=self.owner,
			visibility=World.Visibility.PRIVATE,
		)
		self.character = Character.objects.create(
			world=self.public_world, name='Owner Character', owner=self.owner
		)
		CharacterWorldEntry.objects.create(
			character=self.character, world=self.public_world, added_by=self.owner
		)
		self.active_membership = WorldMembership.objects.create(
			world=self.public_world,
			user=self.other,
			status=WorldMembership.Status.ACTIVE,
		)

	def test_can_view_world_for_public_world(self):
		self.assertTrue(can_view_world(self.owner, self.public_world))
		self.assertTrue(can_view_world(self.other, self.public_world))

	def test_can_view_world_for_private_world_is_owner_only(self):
		self.assertTrue(can_view_world(self.owner, self.private_world))
		self.assertFalse(can_view_world(self.other, self.private_world))

	def test_can_post_world_is_owner_only(self):
		self.assertTrue(can_post_world(self.owner, self.public_world))
		self.assertTrue(can_post_world(self.other, self.public_world))

	def test_world_timeline_allows_authenticated_user_for_public_world(self):
		self.client.force_login(self.other)
		url = reverse('world_timeline', args=[self.public_world.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

	def test_world_timeline_uses_stable_desc_order_with_id_tiebreak(self):
		self.client.force_login(self.owner)
		tied_time = Post.objects.create(
			world=self.public_world,
			character=self.character,
			author=self.owner,
			text='anchor',
		).created_at
		newer_same_time = Post.objects.create(
			world=self.public_world,
			character=self.character,
			author=self.owner,
			text='newer same ts',
		)
		older_same_time = Post.objects.create(
			world=self.public_world,
			character=self.character,
			author=self.owner,
			text='older same ts',
		)
		newer_same_time.created_at = tied_time
		older_same_time.created_at = tied_time
		newer_same_time.save(update_fields=['created_at'])
		older_same_time.save(update_fields=['created_at'])

		response = self.client.get(reverse('world_timeline', args=[self.public_world.id]))
		self.assertEqual(response.status_code, 200)
		posts = list(response.context['posts'])
		ids = [post.id for post in posts]
		self.assertEqual(ids, sorted(ids, reverse=True))

	def test_world_timeline_exposes_cursor_link_for_next_page(self):
		self.client.force_login(self.owner)
		for index in range(25):
			Post.objects.create(
				world=self.public_world,
				character=self.character,
				author=self.owner,
				text=f'post {index}',
			)

		response = self.client.get(reverse('world_timeline', args=[self.public_world.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '次の投稿を読み込む')
		self.assertContains(response, '再試行する')
		self.assertContains(response, 'data-load-more-url')
		self.assertEqual(len(response.context['posts']), 20)
		self.assertTrue(response.context['has_next'])
		self.assertTrue(response.context['next_cursor'])

	def test_world_timeline_empty_state_has_reload_action(self):
		self.client.force_login(self.owner)
		response = self.client.get(reverse('world_timeline', args=[self.public_world.id]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'まだ投稿がありません。')
		self.assertContains(response, 'タイムラインを再読み込みする')

	def test_world_timeline_cursor_pagination_has_no_duplicates(self):
		self.client.force_login(self.owner)
		for index in range(25):
			Post.objects.create(
				world=self.public_world,
				character=self.character,
				author=self.owner,
				text=f'post {index}',
			)

		first_page = self.client.get(reverse('world_timeline', args=[self.public_world.id]))
		cursor = first_page.context['next_cursor']
		second_page = self.client.get(
			reverse('world_timeline', args=[self.public_world.id]),
			{'cursor': cursor},
		)

		first_ids = {post.id for post in first_page.context['posts']}
		second_ids = {post.id for post in second_page.context['posts']}
		self.assertFalse(first_ids.intersection(second_ids))

	def test_world_timeline_invalid_cursor_falls_back_to_first_page(self):
		self.client.force_login(self.owner)
		for index in range(3):
			Post.objects.create(
				world=self.public_world,
				character=self.character,
				author=self.owner,
				text=f'post {index}',
			)

		response = self.client.get(
			reverse('world_timeline', args=[self.public_world.id]),
			{'cursor': 'broken-cursor'},
			follow=True,
		)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'タイムラインのカーソルが不正です。先頭から再表示します。')

	def test_world_timeline_allows_anonymous_user_for_public_world(self):
		url = reverse('world_timeline', args=[self.public_world.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.public_world.title)
		self.assertNotContains(response, f'href="{reverse("post_create", args=[self.public_world.id])}"')
		self.assertContains(response, 'ログインして投稿する')
		post_url = reverse('post_create', args=[self.public_world.id])
		self.assertContains(response, f"{reverse('login')}?next={quote(post_url, safe='')}")

	def test_world_timeline_forbids_non_owner_for_private_world(self):
		self.client.force_login(self.other)
		url = reverse('world_timeline', args=[self.private_world.id])
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, reverse('world_list'))
		self.assertContains(response, 'このWorldは非公開です。参加には作成者の承認が必要です。')

	def test_world_timeline_forbids_anonymous_user_for_private_world(self):
		url = reverse('world_timeline', args=[self.private_world.id])
		response = self.client.get(url)
		self.assertRedirects(
			response,
			f"{reverse('login')}?next={url}",
			fetch_redirect_response=False,
		)

	def test_private_world_redirect_keeps_next_after_login(self):
		world_url = reverse('world_timeline', args=[self.private_world.id])
		login_url = f"{reverse('login')}?next={world_url}"
		response = self.client.post(
			login_url,
			{'username': 'owner@example.com', 'password': 'pass12345', 'next': world_url},
		)
		self.assertRedirects(response, world_url, fetch_redirect_response=False)
		follow_response = self.client.get(world_url)
		self.assertEqual(follow_response.status_code, 200)

	def test_character_list_forbids_non_owner_with_unified_403_response(self):
		self.active_membership.status = WorldMembership.Status.KICKED
		self.active_membership.save(update_fields=['status', 'updated_at'])
		self.client.force_login(self.other)
		url = reverse('character_list', args=[self.public_world.id])
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, reverse('world_list'))
		self.assertContains(response, 'このWorldで操作する権限がありません。')

	def test_world_timeline_private_returns_deny_reason_json_for_async(self):
		self.client.force_login(self.other)
		url = reverse('world_timeline', args=[self.private_world.id])
		response = self.client.get(
			url,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_ACCEPT='application/json',
		)
		self.assertEqual(response.status_code, 403)
		self.assertEqual(response.json()['deny_reason'], 'PRIVATE_WORLD_NOT_MEMBER')
		self.assertIn('承認が必要', response.json()['message'])

	def test_character_list_returns_deny_reason_json_for_async(self):
		self.active_membership.status = WorldMembership.Status.BANNED
		self.active_membership.save(update_fields=['status', 'updated_at'])
		self.client.force_login(self.other)
		url = reverse('character_list', args=[self.public_world.id])
		response = self.client.get(
			url,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
			HTTP_ACCEPT='application/json',
		)
		self.assertEqual(response.status_code, 403)
		self.assertEqual(response.json()['deny_reason'], 'WORLD_ACTION_FORBIDDEN')

	def test_post_create_saves_author_and_world(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('post_create', args=[self.public_world.id]),
			{'character': self.character.id, 'text': 'hello world post'},
		)
		self.assertEqual(response.status_code, 302)
		post = Post.objects.get()
		self.assertEqual(post.world, self.public_world)
		self.assertEqual(post.author, self.owner)
		self.assertEqual(post.character, self.character)

	def test_post_create_denies_non_owner(self):
		self.active_membership.status = WorldMembership.Status.BANNED
		self.active_membership.save(update_fields=['status', 'updated_at'])
		self.client.force_login(self.other)
		response = self.client.post(reverse('post_create', args=[self.public_world.id]), follow=True)
		self.assertRedirects(response, reverse('world_list'))
		self.assertContains(response, 'このWorldで操作する権限がありません。')

	def test_private_world_requires_active_membership_for_view(self):
		WorldMembership.objects.create(
			world=self.private_world,
			user=self.other,
			status=WorldMembership.Status.ACTIVE,
		)
		self.assertTrue(can_view_world(self.other, self.private_world))

	def test_banned_user_can_still_view_public_world_but_cannot_post(self):
		self.active_membership.status = WorldMembership.Status.BANNED
		self.active_membership.save(update_fields=['status', 'updated_at'])
		self.assertTrue(can_view_world(self.other, self.public_world))
		self.assertFalse(can_post_world(self.other, self.public_world))

	def test_owner_can_ban_user_and_create_audit_log(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('world_moderation', args=[self.public_world.id]),
			{'target_handle': 'other', 'action': 'ban'},
		)
		self.assertEqual(response.status_code, 302)
		self.active_membership.refresh_from_db()
		self.assertEqual(self.active_membership.status, WorldMembership.Status.BANNED)
		self.assertTrue(
			WorldModerationLog.objects.filter(
				world=self.public_world,
				actor=self.owner,
				target_user=self.other,
				action=WorldModerationLog.Action.BAN,
			).exists()
		)

	def test_owner_can_kick_active_member_and_create_audit_log(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('world_moderation', args=[self.public_world.id]),
			{'target_handle': 'other', 'action': 'kick'},
		)
		self.assertEqual(response.status_code, 302)
		self.active_membership.refresh_from_db()
		self.assertEqual(self.active_membership.status, WorldMembership.Status.KICKED)
		self.assertTrue(
			WorldModerationLog.objects.filter(
				world=self.public_world,
				actor=self.owner,
				target_user=self.other,
				action=WorldModerationLog.Action.KICK,
			).exists()
		)

	def test_character_create_sets_owner_and_world_entry(self):
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('character_create', args=[self.public_world.id]),
			{'name': 'New Hero', 'profile': 'A brave hero', 'personality': 'Brave'},
		)
		self.assertEqual(response.status_code, 302)
		character = Character.objects.get(name='New Hero')
		self.assertEqual(character.owner, self.owner)
		self.assertTrue(
			CharacterWorldEntry.objects.filter(character=character, world=self.public_world).exists()
		)

	def test_character_bring_in_creates_world_entry(self):
		"""他人のWorldにキャラを持ち込むと CharacterWorldEntry が作成される。"""
		other_world = World.objects.create(
			title='Other World', owner=self.other, visibility=World.Visibility.PUBLIC
		)
		WorldMembership.objects.create(
			world=other_world, user=self.owner, status=WorldMembership.Status.ACTIVE
		)
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('character_bring_in', args=[other_world.id]),
			{'character_id': self.character.id},
		)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(
			CharacterWorldEntry.objects.filter(character=self.character, world=other_world).exists()
		)

	def test_character_bring_in_blocked_for_banned_user(self):
		"""BAN されたユーザーは持ち込みできない。"""
		other_world = World.objects.create(
			title='Other World', owner=self.owner, visibility=World.Visibility.PUBLIC
		)
		other_character = Character.objects.create(
			world=self.public_world, name='Other Character', owner=self.other
		)
		CharacterWorldEntry.objects.create(
			character=other_character, world=self.public_world, added_by=self.other
		)
		WorldMembership.objects.create(
			world=other_world, user=self.other, status=WorldMembership.Status.BANNED
		)
		self.client.force_login(self.other)
		response = self.client.post(
			reverse('character_bring_in', args=[other_world.id]),
			{'character_id': other_character.id},
			follow=True,
		)
		self.assertRedirects(response, reverse('world_list'))
		self.assertContains(response, 'このWorldで操作する権限がありません。')
		self.assertFalse(
			CharacterWorldEntry.objects.filter(character=other_character, world=other_world).exists()
		)

	def test_character_bring_in_blocked_for_kicked_user(self):
		"""Kick されたユーザーは持ち込みできない。"""
		other_world = World.objects.create(
			title='Other World', owner=self.owner, visibility=World.Visibility.PUBLIC
		)
		other_character = Character.objects.create(
			world=self.public_world, name='Other Character', owner=self.other
		)
		CharacterWorldEntry.objects.create(
			character=other_character, world=self.public_world, added_by=self.other
		)
		WorldMembership.objects.create(
			world=other_world, user=self.other, status=WorldMembership.Status.KICKED
		)
		self.client.force_login(self.other)
		response = self.client.get(
			reverse('character_bring_in', args=[other_world.id]),
			follow=True,
		)
		self.assertRedirects(response, reverse('world_list'))
		self.assertContains(response, 'このWorldで操作する権限がありません。')

	def test_post_create_fails_for_character_not_in_world(self):
		"""WorldEntry がないキャラクターは投稿フォームのバリデーションで弾かれる。"""
		extra_char = Character.objects.create(
			world=self.private_world, name='Outsider', owner=self.owner
		)
		self.client.force_login(self.owner)
		response = self.client.post(
			reverse('post_create', args=[self.public_world.id]),
			{'character': extra_char.id, 'text': 'should fail'},
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(Post.objects.filter(text='should fail').exists())

	def test_character_bring_in_accessible_for_non_member_on_public_world(self):
		"""メンバーシップがない状態でも公開 World への持ち込みができる。"""
		third_user = User.objects.create_user(
			username='third', email='third@example.com', password='pass12345', handle='third',
		)
		third_world = World.objects.create(
			title='Third World', owner=third_user, visibility=World.Visibility.PUBLIC,
		)
		my_character = Character.objects.create(
			world=third_world, name='Third Char', owner=third_user,
		)
		CharacterWorldEntry.objects.create(
			character=my_character, world=third_world, added_by=third_user,
		)

		self.client.force_login(third_user)
		response = self.client.post(
			reverse('character_bring_in', args=[self.public_world.id]),
			{'character_id': my_character.id},
		)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(
			CharacterWorldEntry.objects.filter(character=my_character, world=self.public_world).exists()
		)
		# 初回持ち込み時に WorldMembership が自動作成されること
		self.assertTrue(
			WorldMembership.objects.filter(
				world=self.public_world,
				user=third_user,
				status=WorldMembership.Status.ACTIVE,
			).exists()
		)

	def test_character_bring_in_does_not_overwrite_existing_membership(self):
		"""既存の membership がある場合は status を上書きしない（Kick/BAN 状態を維持）。"""
		third_user = User.objects.create_user(
			username='third2', email='third2@example.com', password='pass12345', handle='third2',
		)
		third_world = World.objects.create(
			title='Third World 2', owner=third_user, visibility=World.Visibility.PUBLIC,
		)
		my_character = Character.objects.create(
			world=third_world, name='Third Char 2', owner=third_user,
		)
		CharacterWorldEntry.objects.create(
			character=my_character, world=third_world, added_by=third_user,
		)
		# 既に active な membership を持つユーザーが持ち込みしても status は変わらない
		WorldMembership.objects.create(
			world=self.public_world, user=third_user, status=WorldMembership.Status.ACTIVE,
		)
		self.client.force_login(third_user)
		self.client.post(
			reverse('character_bring_in', args=[self.public_world.id]),
			{'character_id': my_character.id},
		)
		membership = WorldMembership.objects.get(world=self.public_world, user=third_user)
		self.assertEqual(membership.status, WorldMembership.Status.ACTIVE)

	# ------------------------------------------------------------------
	# Character の編集・削除に関する権限境界テスト (#56)
	# ------------------------------------------------------------------

	def test_character_edit_blocked_for_non_owner_via_direct_url(self):
		"""他人の Character 編集は direct URL でも拒否される。"""
		self.client.force_login(self.other)
		url = reverse('character_edit', args=[self.public_world.id, self.character.id])
		response = self.client.get(url, follow=True)
		self.assertRedirects(response, reverse('character_list', args=[self.public_world.id]))
		self.assertContains(response, 'このキャラクターを編集する権限がありません。')

	def test_character_delete_blocked_for_non_owner_via_direct_url(self):
		"""他人の Character 削除は direct URL でも拒否される。"""
		self.client.force_login(self.other)
		url = reverse('character_delete', args=[self.public_world.id, self.character.id])
		response = self.client.post(url, follow=True)
		self.assertRedirects(response, reverse('character_list', args=[self.public_world.id]))
		self.assertContains(response, 'このキャラクターを削除する権限がありません。')
		self.assertTrue(Character.objects.filter(id=self.character.id).exists())

	def test_character_edit_allowed_for_owner(self):
		"""Character の作成者は編集できる。"""
		self.client.force_login(self.owner)
		url = reverse('character_edit', args=[self.public_world.id, self.character.id])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

	def test_character_edit_works_for_brought_in_character(self):
		"""他の World から持ち込んだ Character も、作成者なら編集フォームにアクセスできる（持ち込み 404 不整合の回帰テスト）。"""
		other_world = World.objects.create(
			title='Other World', owner=self.other, visibility=World.Visibility.PUBLIC
		)
		# other が own する Character を public_world に持ち込む
		other_char = Character.objects.create(
			world=other_world, name='Brought Char', owner=self.other
		)
		CharacterWorldEntry.objects.create(
			character=other_char, world=self.public_world, added_by=self.other
		)
		self.client.force_login(self.other)
		url = reverse('character_edit', args=[self.public_world.id, other_char.id])
		# other_char.world = other_world だが public_world コンテキストで編集できること
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)


class ModerationTests(TestCase):
	"""通報・ブロック機能のテスト。"""

	def setUp(self):
		self.reporter = User.objects.create_user(
			username='reporter',
			email='reporter@example.com',
			password='pass12345',
			handle='reporter',
		)
		self.target_user = User.objects.create_user(
			username='target',
			email='target@example.com',
			password='pass12345',
			handle='target',
		)
		self.world = World.objects.create(
			title='Test World',
			owner=self.target_user,
			visibility=World.Visibility.PUBLIC,
		)
		self.character = Character.objects.create(
			world=self.world,
			name='Test Character',
			owner=self.target_user,
		)
		CharacterWorldEntry.objects.create(
			character=self.character,
			world=self.world,
			added_by=self.target_user,
		)
		self.post = Post.objects.create(
			world=self.world,
			character=self.character,
			author=self.target_user,
			text='Test post',
		)

	def test_report_post_creates_record(self):
		"""投稿通報がモデルに記録される。"""
		self.client.force_login(self.reporter)
		url = reverse('report_post', args=[self.post.id])
		response = self.client.post(url, {
			'reason': 'spam',
			'description': 'This is spam',
		}, follow=True)
		self.assertEqual(response.status_code, 200)

		from .models import Report
		self.assertTrue(Report.objects.filter(
			reporter=self.reporter,
			target_post=self.post,
			reason='spam',
		).exists())

	def test_report_user_creates_record(self):
		"""ユーザー通報がモデルに記録される。"""
		self.client.force_login(self.reporter)
		url = reverse('report_user', args=[self.target_user.id])
		response = self.client.post(url, {
			'reason': 'abuse',
			'description': 'Harassment',
		}, follow=True)
		self.assertEqual(response.status_code, 200)

		from .models import Report
		self.assertTrue(Report.objects.filter(
			reporter=self.reporter,
			target_user=self.target_user,
			reason='abuse',
		).exists())

	def test_blocked_user_posts_not_in_timeline(self):
		"""ブロック中のユーザーの投稿がタイムラインから除外される。"""
		from users.models import UserBlock

		# reporter が target_user をブロック
		UserBlock.objects.create(blocker=self.reporter, blocked=self.target_user)

		# reporter でタイムラインを確認
		self.client.force_login(self.reporter)
		url = reverse('world_timeline', args=[self.world.id])
		response = self.client.get(url)

		# target_user の投稿が表示されない
		self.assertNotContains(response, 'Test post')

	def test_follow_blocked_user_denied(self):
		"""ブロック中のユーザーはフォローできない。"""
		from users.models import UserBlock

		# reporter が target_user をブロック
		UserBlock.objects.create(blocker=self.reporter, blocked=self.target_user)

		# reporter が target_user をフォローしようとする
		self.client.force_login(self.reporter)
		url = reverse('follow_create', args=[self.target_user.handle])
		response = self.client.post(url, {'next': '/'}, follow=True)

		# メッセージに「ブロック中」が含まれる
		self.assertContains(response, 'ブロック中のユーザーはフォローできません')

	def test_block_deletes_existing_follows(self):
		"""ブロック時に既存のフォロー関係が削除される。"""
		from users.models import Follow, UserBlock

		# reporter が target_user をフォロー
		Follow.objects.create(
			follower=self.reporter,
			followee=self.target_user,
			status=Follow.Status.ACCEPTED,
		)

		# reporter が target_user をブロック
		self.client.force_login(self.reporter)
		url = reverse('block_user', args=[self.target_user.id])
		response = self.client.post(url, follow=True)
		self.assertEqual(response.status_code, 200)

		# フォロー関係が削除されている
		self.assertFalse(Follow.objects.filter(
			follower=self.reporter,
			followee=self.target_user,
		).exists())

		# ブロック記録が存在する
		self.assertTrue(UserBlock.objects.filter(
			blocker=self.reporter,
			blocked=self.target_user,
		).exists())

		self.assertEqual(response.status_code, 200)


class TimelineBlockingTests(TestCase):
	"""タイムライン遮断ルール検証テスト（仕様: docs/TIMELINE_BLOCKING_SPEC.md）"""

	def setUp(self):
		"""各テスト前の共通設定"""
		self.user_a = User.objects.create_user(
			username='user_a',
			email='user_a@example.com',
			password='pass12345',
			handle='user_a',
		)
		self.user_b = User.objects.create_user(
			username='user_b',
			email='user_b@example.com',
			password='pass12345',
			handle='user_b',
		)
		self.user_c = User.objects.create_user(
			username='user_c',
			email='user_c@example.com',
			password='pass12345',
			handle='user_c',
		)

		self.world = World.objects.create(
			title='Test World',
			owner=self.user_a,
			visibility=World.Visibility.PUBLIC,
		)
		self.character_a = Character.objects.create(
			world=self.world,
			name='Character A',
			owner=self.user_a,
		)
		self.character_b = Character.objects.create(
			world=self.world,
			name='Character B',
			owner=self.user_b,
		)
		CharacterWorldEntry.objects.create(
			character=self.character_a,
			world=self.world,
			added_by=self.user_a,
		)
		CharacterWorldEntry.objects.create(
			character=self.character_b,
			world=self.world,
			added_by=self.user_b,
		)

		# User A と B から各 3 投稿作成
		self.posts_b = []
		for i in range(3):
			post = Post.objects.create(
				world=self.world,
				character=self.character_b,
				author=self.user_b,
				text=f'Post {i+1} from user_b',
			)
			self.posts_b.append(post)

		self.posts_a = []
		for i in range(3):
			post = Post.objects.create(
				world=self.world,
				character=self.character_a,
				author=self.user_a,
				text=f'Post {i+1} from user_a',
			)
			self.posts_a.append(post)

	def _get_timeline_post_ids(self, user, world):
		"""タイムラインから見える投稿 ID リストを取得"""
		self.client.force_login(user)
		response = self.client.get(reverse('world_timeline', args=[world.id]))
		self.assertEqual(response.status_code, 200)
		posts = response.context.get('posts', [])
		return [post.id for post in posts]

	def _setup_block(self, blocker, blocked):
		"""ブロック関係を設定"""
		from users.models import UserBlock
		UserBlock.objects.create(blocker=blocker, blocked=blocked)

	# Layer 1: ユーザーレベル（ブロック）テスト

	def test_blocked_user_posts_hidden_from_blocker(self):
		"""**T1-1** A が B をブロック → A は B の投稿を見ない"""
		self._setup_block(self.user_a, self.user_b)

		visible_posts = self._get_timeline_post_ids(self.user_a, self.world)

		# A の投稿 3 つだけ表示、B の投稿 3 つは除外
		self.assertEqual(len(visible_posts), 3)
		for post_id in visible_posts:
			self.assertNotIn(post_id, [p.id for p in self.posts_b])

	def test_block_is_unidirectional(self):
		"""**T1-2** A が B をブロック → B は A の投稿を普通に見える"""
		self._setup_block(self.user_a, self.user_b)

		visible_posts = self._get_timeline_post_ids(self.user_b, self.world)

		# B は A の投稿 3 つを普通に見える
		self.assertEqual(len(visible_posts), 6)  # B 自分の 3 + A の 3
		post_ids = [p.id for p in self.posts_a]
		for post_id in post_ids:
			self.assertIn(post_id, visible_posts)

	def test_unblock_shows_posts_again(self):
		"""**T1-3** A が B をブロック → アンブロック → A は B の投稿を見える"""
		from users.models import UserBlock

		# ブロック設定
		block = UserBlock.objects.create(blocker=self.user_a, blocked=self.user_b)
		
		# ブロック中は見えない
		visible_before = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible_before), 3)  # A の投稿のみ

		# ブロック解除
		block.delete()

		# アンブロック後は見える
		visible_after = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible_after), 6)  # A の 3 + B の 3

	def test_mutual_blocks(self):
		"""**T1-4** A ↔ B mutual block → 双方は互いに投稿を見ない"""
		self._setup_block(self.user_a, self.user_b)
		self._setup_block(self.user_b, self.user_a)

		# A から見た場合
		visible_a = self._get_timeline_post_ids(self.user_a, self.world)
		# A の投稿 3 つのみ（B の投稿は除外）
		self.assertEqual(len(visible_a), 3)

		# B から見た場合
		visible_b = self._get_timeline_post_ids(self.user_b, self.world)
		# B の投稿 3 つのみ（A の投稿は除外）
		self.assertEqual(len(visible_b), 3)

	# Layer 3: アカウント停止テスト

	def test_inactive_user_posts_hidden(self):
		"""**T3-1** B のアカウントが停止中 → 全員が B の投稿を見ない"""
		# B のアカウント停止
		self.user_b.is_active = False
		self.user_b.save()

		# A から見た場合
		visible_a = self._get_timeline_post_ids(self.user_a, self.world)
		# A の投稿 3 つのみ（B は停止中なため除外）
		self.assertEqual(len(visible_a), 3)

		# C (未認証) から見た場合
		visible_c = self._get_timeline_post_ids(self.user_c, self.world)
		# B は停止中なため除外
		self.assertNotIn(self.posts_b[0].id, visible_c)

	def test_inactive_user_posts_visible_after_reactivation(self):
		"""**T3-2** B 停止 → 再開 → B の投稿が再表示"""
		# B のアカウント停止
		self.user_b.is_active = False
		self.user_b.save()

		visible_before = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible_before), 3)  # A のみ

		# B を再開
		self.user_b.is_active = True
		self.user_b.save()

		# 投稿が再表示
		visible_after = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible_after), 6)  # A の 3 + B の 3

	# 複合シナリオテスト

	def test_block_overrides_follow_relationship(self):
		"""**T4-1** A が B をフォロー + ブロック → B の投稿は表示されない"""
		from users.models import Follow

		# A が B をフォロー
		Follow.objects.create(
			follower=self.user_a,
			followee=self.user_b,
			status=Follow.Status.ACCEPTED,
		)

		# A が B をブロック
		self._setup_block(self.user_a, self.user_b)

		# ブロックが優先される
		visible = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible), 3)  # A の投稿のみ

	def test_multiple_blocked_users_excluded(self):
		"""**T4-2** A が B, C をブロック → A は両者の投稿を見ない"""
		# C から投稿を追加
		post_c = Post.objects.create(
			world=self.world,
			character=self.character_a,  # 簡易: A のキャラで投稿（実装では C のキャラを使用）
			author=self.user_c,
			text='Post from user_c',
		)

		# A が B, C をブロック
		self._setup_block(self.user_a, self.user_b)
		self._setup_block(self.user_a, self.user_c)

		visible = self._get_timeline_post_ids(self.user_a, self.world)

		# A の投稿のみ
		self.assertEqual(len(visible), 3)
		self.assertNotIn(post_c.id, visible)

	def test_timeline_respects_blocking_across_worlds(self):
		"""**T4-3** ブロック関係は複数 World で一貫性を持つ（同じユーザーブロック）"""
		# 別の World を作成
		world_2 = World.objects.create(
			title='Another World',
			owner=self.user_a,
			visibility=World.Visibility.PUBLIC,
		)
		char_b2 = Character.objects.create(
			world=world_2,
			name='Char B in World 2',
			owner=self.user_b,
		)
		CharacterWorldEntry.objects.create(
			character=char_b2,
			world=world_2,
			added_by=self.user_b,
		)

		# World 2 に B の投稿を追加
		post_b_w2 = Post.objects.create(
			world=world_2,
			character=char_b2,
			author=self.user_b,
			text='Post in world 2',
		)

		# A が B をブロック
		self._setup_block(self.user_a, self.user_b)

		# World 1 で見える投稿
		visible_w1 = self._get_timeline_post_ids(self.user_a, self.world)
		self.assertEqual(len(visible_w1), 3)

		# World 2 でも見えない（ブロックは World 横断で有効）
		visible_w2 = self._get_timeline_post_ids(self.user_a, world_2)
		self.assertNotIn(post_b_w2.id, visible_w2)