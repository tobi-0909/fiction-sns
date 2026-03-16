# タイムライン主要クエリのインデックス戦略（M4-12）

## 1. 対象クエリ

### 1-1. World タイムライン（first page / cursor page）
- 条件: world_id で絞り込み
- 並び順: created_at DESC, id DESC
- カーソル条件: (created_at < x) OR (created_at = x AND id < y)

### 1-2. プロフィール最近投稿
- 条件: author_id で絞り込み
- 並び順: created_at DESC

### 1-3. フォロー一覧 / フォロワー一覧
- 条件: follower または followee + status
- 並び順: accepted_at DESC, created_at DESC

## 2. 採用インデックス

### 2-1. Post
- idx_post_world_timeline: (world_id, created_at DESC, id DESC)
  - 目的: タイムライン取得の sort/cursor を同一インデックスで処理
- idx_post_author_recent: (author_id, created_at DESC)
  - 目的: プロフィール最近投稿の取得を安定化

### 2-2. Follow
- idx_following_list: (follower_id, status, accepted_at DESC, created_at DESC)
  - 目的: フォロー中一覧の取得コストを抑制
- idx_follower_list: (followee_id, status, accepted_at DESC, created_at DESC)
  - 目的: フォロワー一覧の取得コストを抑制

## 3. 変更前後の実測（ローカル）

計測条件:
- コマンド: python manage.py benchmark_timeline --post-count 400 --runs 20
- データ: benchmark world の投稿数 400 件

変更前（index追加前）:
- first_page: p95=21.94ms, avg=10.93ms, max=46.20ms, avg_queries=2.00, error_rate=0.00%
- cursor_page: p95=6.09ms, avg=5.01ms, max=6.57ms, avg_queries=2.00, error_rate=0.00%

変更後（index追加後）:
- first_page: p95=4.98ms, avg=5.12ms, max=20.95ms, avg_queries=2.00, error_rate=0.00%
- cursor_page: p95=4.65ms, avg=4.32ms, max=4.96ms, avg_queries=2.00, error_rate=0.00%

## 4. 判定
- p95 / query count / error rate は TIMELINE_SLO の閾値を満たす
- #69 の受け入れ条件
  - [x] 主要クエリとインデックス方針が文書化された
  - [x] 変更前後の実測比較結果が残った

## 5. 注意
- ローカルSQLiteの値は相対比較として扱う
- 本番環境では #74（公開環境）完了後に同条件で再計測し、必要なら閾値を調整する
