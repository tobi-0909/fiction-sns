# タイムライン取得仕様（M4-07）

この文書は、World タイムラインの取得仕様を固定するためのものです。

## 1. 取得方式
- 方式: カーソル方式（cursor pagination）
- 対象URL: /worlds/<world_id>/timeline/
- クエリ: cursor（任意）

初回アクセスは cursor なしで先頭ページを返す。

## 2. 順序保証ルール
- ソート順: created_at DESC, id DESC
- 同一 created_at の投稿は id の降順で決定的に並べる
- 次ページ条件: 
  - created_at < cursor.created_at
  - または created_at == cursor.created_at かつ id < cursor.id

これにより同時刻投稿が存在しても、重複・取りこぼしを防ぐ。

## 3. カーソル形式
- 形式: <created_at ISO8601>|<post_id>
- 例: 2026-03-16T09:10:11.123456+00:00|123

不正カーソルが来た場合は先頭ページにフォールバックし、画面メッセージを表示する。

## 4. ページング契約（UI）
- 1ページ件数: 20件
- サーバは has_next, next_cursor をテンプレートへ渡す
- has_next が true の場合のみ「次の投稿を読み込む」リンクを表示
- 次ページURL: /worlds/<world_id>/timeline/?cursor=<next_cursor>

## 5. 実装・テスト観点
- [x] 同時刻投稿で順序が崩れない
- [x] 次ページで重複が発生しない
- [x] 不正カーソル時に先頭へフォールバック
- [x] next_cursor がある場合のみUIリンクを表示

## 6. 次段（関連Issue）
- #67: SLO定義と計測手順
- #69: クエリ最適化と実測
- #68: モバイル回線のUX改善
