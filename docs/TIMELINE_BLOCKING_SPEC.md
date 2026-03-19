# タイムライン遮断仕様書

**最終更新: 2026年3月19日**

**関連ドキュメント:**
- [モデレーション・安全運用ガイド](MODERATION.md) - ブロック・通報基本機能
- [コンプライアンス対応手順書](COMPLIANCE_PROCEDURES.md) - 違法コンテンツ対応
- [インシデント対応手順書](INCIDENT_RESPONSE.md) - 重大インシデント対応

## 1. 概要

fiction-sns においてタイムラインに表示される投稿は、ブロック・通報・削除などのモデレーション状態に応じて適切に除外される必要があります。

本ドキュメントは、**誰がどのような状態の投稿を見るべきか/見るべきでないか** を統合的に定義し、実装基準とテスト観点を明確にします。

## 2. 遮断ルール定義（3層）

### Layer 1: ユーザーレベル（ブロック）

**ルール 1-1: 一方向ブロック**

```
ブロック関係: UserBlock(blocker → blocked)

A が B をブロック
  ├─ A は B の投稿を見ない（タイムラインで除外）
  ├─ A は B をフォローできない（既存フォロー削除）
  ├─ B が A をフォローしている場合は削除
  └─ B は A の投稿を見える（ブロックは一方向）
```

**実装場所**: `worlds/views.py::world_timeline()` の exclude フィルタ

```python
if request.user.is_authenticated:
    from users.models import UserBlock
    blocked_user_ids = UserBlock.objects.filter(
        blocker=request.user
    ).values_list('blocked_id', flat=True)
    base_posts = base_posts.exclude(author_id__in=blocked_user_ids)
```

**既存テスト**: `worlds/tests.py::ModerationTests::test_blocked_user_posts_not_in_timeline`

---

### Layer 2: World レベル（投稿削除）

**ルール 2-1: 投稿削除（Owner が明示的に削除）**

```
削除対象: Post.deleted_at is not None の投稿

削除された投稿
  ├─ Owner が削除 可能（Post.author == World.owner ⇒ 削除権）
  ├─ 全ユーザーは削除投稿を見ない
  ├─ コンテンツ違反の通報も投稿削除で対応可能
  └─ 削除投稿はテンプレートで「削除されました」と表示
```

**実装状況**: 

- ⚠️ `Post` モデルに `deleted_at` フィールドの有無を確認必要
- ⚠️ `world_timeline` で削除フィルタができているか確認必要

---

### Layer 3: システムレベル（アカウント停止・削除）

**ルール 3-1: アカウント停止**

```
停止状態: CustomUser.is_active = False

停止中のユーザー
  ├─ 投稿は全タイムラインから非表示化
  ├─ World owner が停止中のユーザーをメンバーから削除可能（Phase 2）
  ├─ フォロー・フォロワー一覧から除外
  └─ プロフィームページにアクセス不可（Project 要件を確認 Phase 2）
```

**実装状況**:

- ✅ Django の `is_active` フィールドは存在
- ⚠️ `world_timeline` で `author__is_active=True` フィルタが不足している可能性

```python
# 推奨実装
base_posts = base_posts.filter(author__is_active=True)
```

---

**ルール 3-2: アカウント削除**

```
削除状態: CustomUser.is_deleted = True (Phase 2 で実装)

削除済みユーザー
  ├─ 投稿は全タイムラインから非表示化
  ├─ プロフィール表示不可
  ├─ フォロー・メッセージの処理は Phase 2 で定義
  └─ GDPR compliance: 削除日から 30 日後に物理削除
```

**実装状況**: Phase 2（本 Issue スコープ外）

---

## 3. ユースケース別テーブル

**表記法:**
- ✅ 見える
- ❌ 見えない

### 3.1 基本シナリオ

| Case | シナリオ | 閲覧者 | 投稿者 | 状態 | 閲覧者が見る？ | 理由 |
|------|---------|--------|--------|------|--------------|------|
| Case 1 | 通常投稿 | A | B | 通常 | ✅ | 制限なし |
| Case 2 | ブロック（一方向） | A | B | A が B をブロック | ❌ | Layer 1: ブロック除外 |
| Case 3 | ブロック（逆向） | A | B | B が A をブロック | ✅ | ブロックは一方向のため |
| Case 4 | 投稿削除 | A | B | B が B の投稿を削除 | ❌ | Layer 2: 削除投稿フィルタ |
| Case 5 | アカウント停止 | A | B | B のアカウントが停止中 | ❌ | Layer 3: is_active=False |
| Case 6 | ブロック + 投稿削除 | A | B | A が B をブロック＋B 投稿削除 | ❌ | いずれかで除外 |

### 3.2 複合シナリオ

| Case | シナリオ | 閲覧者A | 投稿者B | 状態 | A が見る？ | 理由 |
|------|---------|---------|---------|------|-----------|------|
| Case 7 | mutual block | A | B | A→B, B→A | ❌ | A はブロック中だから |
| Case 8 | block → unblock | A | B | A→B → unblock | ✅ | Block release |
| Case 9 | Follow + Block | A | B | A が B をフォロー中に B をブロック | ❌ | ブロックが優先 |
| Case 10 | Private World | A | B | A はメンバーでない、B が投稿 | ❌ | World アクセス権で制御（別層） |

---

## 4. テスト観点定義

### 4.1 テストマトリックス

**テストクラス: `TimelineBlockingTests`**

#### Group: Layer 1 (ユーザーレベル)

| Test ID | テスト名 | 前提条件 | 操作 | 期待値 | 優先度 |
|---------|---------|---------|------|--------|--------|
| T1-1 | `test_blocked_user_posts_hidden` | A が B をブロック | A が world_timeline にアクセス | B の投稿は除外 | 🔴 P1 |
| T1-2 | `test_block_is_unidirectional` | A が B をブロック | B が world_timeline にアクセス | A の投稿は表示 | 🔴 P1 |
| T1-3 | `test_unblock_shows_posts_again` | A が B をブロック → unblock | A が world_timeline にアクセス | B の投稿表示 | 🟡 P2 |
| T1-4 | `test_mutual_blocks` | A ↔ B mutual block | 双方が world_timeline にアクセス | 互いに投稿非表示 | 🟡 P2 |

#### Group: Layer 2 (投稿削除)

| Test ID | テスト名 | 前提条件 | 操作 | 期待値 | 優先度 |
|---------|---------|---------|------|--------|--------|
| T2-1 | `test_deleted_post_not_in_timeline` | B が投稿を削除 | 全ユーザーが world_timeline | 削除投稿は表示されない | 🔴 P1 |
| T2-2 | `test_deleted_post_shows_placeholder` | B が投稿を削除 | HTML テンプレート確認 | 「削除されました」等プレース | 🟡 P2 |

#### Group: Layer 3 (アカウント停止)

| Test ID | テスト名 | 前提条件 | 操作 | 期待値 | 優先度 |
|---------|---------|---------|------|--------|--------|
| T3-1 | `test_inactive_user_posts_hidden` | B の is_active=False | A が world_timeline | B の投稿は表示されない | 🔴 P1 |
| T3-2 | `test_reactive_user_posts_visible` | B の is_active=False → True | A が world_timeline | B の投稿が再表示 | 🟡 P2 |

#### Group: 複合シナリオ

| Test ID | テスト名 | 前提条件 | 操作 | 期待値 | 優先度 |
|---------|---------|---------|------|--------|--------|
| T4-1 | `test_block_overrides_follow` | A が B をフォロー + ブロック | A が world_timeline | B の投稿は表示されない | 🟡 P2 |
| T4-2 | `test_multiple_blocked_users` | A が B, C, D をブロック | A が world_timeline（20投稿） | B, C, D の投稿は全て除外 | 🟡 P2 |

---

### 4.2 テスト前提条件テンプレート

```python
class TimelineBlockingTests(TestCase):
    """タイムライン遮断ルール検証テスト"""
    
    def setUp(self):
        """各テスト前の共通設定"""
        # ユーザー作成（A, B, C, D）
        # World 作成（public/private 両方）
        # Character 作成
        # Post 作成（各ユーザーから投稿生成）
        pass
    
    def _setup_block(self, blocker, blocked):
        """ブロック関係を設定"""
        from users.models import UserBlock
        UserBlock.objects.create(blocker=blocker, blocked=blocked)
    
    def _get_timeline_post_ids(self, user, world):
        """タイムラインから見える投稿 ID リストを取得"""
        self.client.force_login(user)
        response = self.client.get(reverse('world_timeline', args=[world.id]))
        # response から post_ids を抽出
        return [...]
```

---

## 5. 実装上の注意点

### 5.1 パフォーマンス考慮

**問題**: ブロック除外処理での N+1 クエリ

```python
# ❌ 悪い例
for post in posts:
    blocked_user_ids = UserBlock.objects.filter(blocker=user)
    if post.author_id in blocked_user_ids:
        exclude(...)
```

**解決策**: views.py で一度 fetch

```python
# ✅ 良い例
blocked_user_ids = UserBlock.objects.filter(
    blocker=request.user
).values_list('blocked_id', flat=True)
base_posts = base_posts.exclude(author_id__in=blocked_user_ids)
```

### 5.2 キャッシュ戦略（Phase 2）

- ブロック関係が変わった時のキャッシュ無効化
- Redis キャッシュの活用（ユーザーごとの blocked_user_ids）

### 5.3 監査ログ

- ブロック・アンブロック・投稿削除を記録（WorldModerationLog の拡張）
- 運営が削除判断を追跡できるように

---

## 6. テスト実装上の注意

### 6.1 テンプレート側の検証

テンプレート `world_timeline.html` では以下を確認:

```html
{% for post in posts %}
    {% if post.deleted_at %}
        <p>この投稿は削除されました。</p>
    {% else %}
        <!-- 通常投稿表示 -->
    {% endif %}
{% endfor %}
```

### 6.2 ステータスコード検証

- 削除投稿: テンプレート内で非表示（200 OK）
- ブロック: フィルタで除外（200 OK、投稿数減）
- アカウント停止: フィルタで除外（200 OK、投稿数減）

### 6.3 ページング考慮

- cursor ベースページングで 20 投稿取得
- ブロック・削除で実際の投稿数が少なくなる
- 合計投稿数と表示投稿数の差分テスト例:

```python
def test_timeline_count_with_blocking(self):
    # B の投稿数: 10
    # A がブロック中: 3
    # ⇒ A が見える投稿: 7
    self.assertEqual(len(visible_posts), 7)
```

---

## 7. Phase 2 検討事項

以下は本 Issue スコープ外（Phase 2 で実装）:

- ⏸️ アカウント削除（is_deleted フィールド）
- ⏸️ 投稿の soft delete 実装（Post.deleted_at の追加）
- ⏸️ ブロック申請（プライベートアカウント向け）
- ⏸️ 通報による自動遮断（Algorithm 検討）
- ⏸️ Shadow ban（ユーザー側からは見えるが、他者には見えない）

---

## 8. 改定履歴

| 版 | 日付 | 変更 |
|----|------|------|
| 1.0 | 2026-03-19 | 初版（Issue #70 サポート） |

---

**最後の更新者**: 開発チーム
**次回レビュー予定**: 2026-06-19
