# Project Status

Last updated: 2026-03-15

## Milestone 1 完了（2026-03-15）

達成したこと:
- Python 3.10.9 + venv + Django 5.2.12 のローカル環境構築
- Django プロジェクト起動確認（runserver + GET / 200）
- home アプリとカスタムトップページを接続（Issue #3）
- ドキュメント整備と Issue-first 運用基盤（Issue #5）
- Issue ドリブン開発の運用を開始（Milestone 1 / Issue #1〜#6）

Deferred（次の実装後に再着手）:
- #4 トップページのモバイル可読性 → テンプレート化後に再開

リスクメモ:
- ローカルの `urls.py.py` 命名ミスは今後の新ファイル作成で注意が必要
- `__pycache__` と `db.sqlite3` が初回コミットに含まれた（.gitignore で今後は除外済み）

## 現在の状況
完了:
- Milestone 1 完了

進行中:
- Milestone 2 準備中

未着手:
- 認証機能
- World/Character モデルと CRUD
- タイムライン投稿フロー

## 次の 7 タスク（Milestone 2 に向けて）
1. 認証方式を確定する（Django 標準認証を優先）
2. World モデルを設計する
3. Character モデルを設計する
4. マイグレーション作成と admin 登録
5. World の一覧・作成・編集画面を作る
6. Character の一覧・作成・編集画面を作る
7. モバイル向け最低限 CSS を追加する（#4 の再開条件も兼ねる）

## 意思決定ログ
- 初回リリースは Milestone 1〜3 に集中する
- タイムライン基盤が安定するまで AI 連携は後ろ倒しにする
- #4 モバイル可読性はテンプレート化後に再着手（Deferred）
