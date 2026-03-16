# タイムライン性能ガード・基盤アーキテクチャ（M4-06）

本文書は、SNSとして破綻しない最低限の性能ガードを公開前に組み込むため、N+1防止・ページング・フォロータイムライン構築方針・Push型への移行条件をまとめたものです。

## 1. N+1回避のチェック観点

### 1-1. Django ORM クエリ最適化チェックリスト
新しいViewやクエリ追加時は、以下の観点で N+1 を排除する：

- [ ] **select_related 活用**: 外部キー、OneToOne 関連で都度クエリが発生する場合は select_related() で事前読み込み
  - 例: `Post.objects.select_related('author', 'character', 'world')`
  
- [ ] **prefetch_related 活用**: ManyToMany, reverse ForeignKey で複数取得時に活用
  - 例: `User.objects.prefetch_related('followers', 'following')`
  
- [ ] **only/defer での列制限**: 不要な列は明示的に除外し、ネットワーク・キャッシュ効率を向上
  - 例: `Post.objects.only('id', 'text', 'created_at', 'world_id', 'author_id')`
  
- [ ] **annotate/聚集**: クライアント側でループ計算する代わりに、DB側で集計
  - 例: `World.objects.annotate(post_count=Count('posts'))`

- [ ] **インデックス戦略と実測比較**: 複雑な条件フィルタ・ソートは docs/TIMELINE_INDEX_STRATEGY.md で採用インデックスを確定後、`benchmark_timeline` で実測

### 1-2. テスト・検証方法
- **django-debug-toolbar**: ローカル開発時に Queries タブで実クエリ数を確認
- **ベンチマークコマンド**: `python manage.py benchmark_timeline --post-count <N> --runs <M>` で avg_queries を監視
- **回帰テスト**: 新規クエリ導入後は必ず既存テストを再実行し、query leak がないことを確認

### 1-3. 許容範囲
- **World タイムライン**（first/cursor page 共通）: 平均 3〜5 クエリ
  - 1 クエリ: Post 取得本体
  - 1 クエリ: related（author, character, world）select_related
  - 1 クエリ（オプション）: permission check や追加フィルタ
  
- **フォロー一覧 / フォロワー一覧**: 平均 2〜3 クエリ
  - 1 クエリ: Follow レコード取得
  - 1 クエリ（オプション）: related User select_related

## 2. ページング方針

### 2-1. 確定済み（#66で実装）
- **方式**: カーソル方式（cursor pagination）
- **ソート順**: created_at DESC, id DESC で同一時刻の重複を排除
- **1ページ件数**: 20 件固定
- **カーソル形式**: `<created_at ISO8601>|<post_id>`
- **フォールバック**: 不正カーソルは先頭ページで復帰、warning メッセージ表示

### 2-2. 適用対象
- World タイムライン: ✅ 実装済み（#66）
- フォロー中タイムライン: 🔜 フォロータイムライン実装時に同じ仕様で構築（#59/#60以降）

## 3. FollowタイムラインのPull first設計

### 3-1. 背景
フォロー者が増えると、投稿時に全フォロワーへの fan-out が必須になり、DB/キャッシュ負荷が急増する。
初期段階（ユーザー数 <1000）では Pull first（必要時だけクエリ）でコストを抑える。

### 3-2. Pull first 構築方針（公開直後〜M5初期）
**フォロー中タイムライン API の構裁**：
```sql
SELECT posts.* FROM posts
WHERE posts.author_id IN (
  SELECT followee_id FROM follows
  WHERE follower_id = ? AND status = 'accepted'
  ORDER BY accepted_at DESC
)
ORDER BY posts.created_at DESC, posts.id DESC
LIMIT 20
```

実装上のポイント：
- Follow レコードで followee_id リストを取得（prefetch_related で最適化）
- 取得した followee_id で POST フィルタ（`__author_id__in=`）
- インデックス: `idx_post_author_recent` で author_id 別取得を高速化
- ページング: ← 同じカーソル方式（created_at DESC, id DESC）を使用

### 3-3. Push first への移行条件（#72 Backlog タスク）
**移行判定の閾値**（実測ベース、ローカルから本番へ段階的に検証）：
- ユーザー数が 500 以上、かつ
- フォロー数平均が 50 以上、かつ
- ホーム画面（フォロー中タイムライン）の p95 が定義SLO（400ms）を超過する場合

移行時の構成：
- Feed テーブル（follower_id, created_at, post_id）を導入し、投稿時に fan-out
- フォロー新規追加時の backfill（過去 N 日の投稿を遡及）が必要
- ユーザー削除時の cleanup 処理

## 4. Push型への移行判定

### 4-1. 判定対象Issue
- #72 Backlog: Pull first から Push 移行判定の技術検証

### 4-2. 移行条件（チェックリスト）
- [ ] ローカルで Pull first 最大負荷テスト（ユーザー 500 + フォロー 50 平均）を実施
- [ ] 本番環境（#74完了後）で実ユーザー 100+ での 1 週間本番運用データ取得
- [ ] ホーム画面 p95 > 400ms OR avg_queries > 10 の事象が発生した場合
- [ ] 技術検証と移行 PR 作成（Feed テーブル定義、fan-out ロジック、backfill 機構）
- [ ] テスト追加（新規投稿→ Feed 反映、フォロー追加→ backfill、ユーザー削除→ cleanup）
- [ ] 実装完了後に再度ベンチマーク実施し、p95 改善を確認

### 4-3. 移行判定の責任者
- ローカル検証: 開発者（現在の tobi-0909）
- 本番判定: 運用サポート + ユーザーフィードバック ベース

## 5. サマリー（受け入れ条件ステータス）

#58 完了条件：
- [x] N+1回避のチェック観点が docs に明文化される → 本文書セクション 1
- [x] タイムラインのページング方針が確定する → セクション 2（#66で既に実装）
- [x] FollowタイムラインはPull first で設計方針が決まる → セクション 3
- [x] Push型への移行条件（閾値）がbacklogとして定義される → セクション 4

## 6. 関連Issue・リンク
- #66: タイムライン取得仕様の確定
- #67: タイムライン最低性能SLO定義
- #68: モバイル回線UX改善
- #69: タイムライン主要クエリのインデックス戦略
- #70: モデレーション連動のタイムライン遮断
- #71: 障害時運用Runbook
- #72: Pull first → Push 移行判定の技術検証（Backlog）
- #73: タイムラインとランキング層の責務分離（Backlog）
