# タイムライン最低性能SLOと計測手順（M4-08）

この文書は公開前に最低限守るべきタイムライン性能基準を定義する。

## 1. 対象
- 対象画面: /worlds/<world_id>/timeline/
- 対象ケース:
  - first_page（cursorなし）
  - cursor_page（cursorあり）

## 2. 最低SLO（公開前基準）
- p95 応答時間:
  - first_page: 400ms 以下
  - cursor_page: 400ms 以下
- クエリ数:
  - average_queries: 5.0 以下
  - max_queries: 8 以下
- エラー率:
  - error_rate: 0.0%（runs内でHTTP 200以外が0件）

## 3. 計測コマンド
次のコマンドで再現可能な計測を実行する。

```bash
python manage.py benchmark_timeline --post-count 200 --runs 20
```

出力例:

```text
[timeline benchmark]
dataset_posts=200 runs=20 world_id=1
scenario, p95_ms, avg_ms, max_ms, avg_queries, max_queries, error_rate
first_page, 120.10, 95.33, 140.52, 3.00, 3, 0.00%
cursor_page, 118.22, 92.44, 132.71, 3.00, 3, 0.00%
```

## 4. 判定ルール
- Go:
  - すべてのSLOを満たす
- Conditional Go:
  - p95が閾値超過でも 10%以内、かつ #69 で改善予定が明確
- No-Go:
  - error_rate > 0%
  - または p95が閾値を 10%以上超過
  - または max_queries が 8 を超過

## 5. 計測時の注意
- ローカル計測は相対比較として扱い、絶対値は余裕を持って判断する
- 変更前後で同じ post-count / runs を使う
- #69 でインデックス調整を行う場合は、必ず再計測する

## 6. 関連Issue
- #66: 取得仕様の確定
- #69: インデックス戦略と実測
- #64: M4完了判定
