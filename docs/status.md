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

## Milestone 2 完了（2026-03-15）

達成したこと:
- 認証フローを実装（登録・ログイン・ログアウト）
- カスタムUser導入と識別子設計の反映（email + @handle 運用）
- World モデル + CRUD 画面（一覧・作成・編集・削除）
- Character モデル + CRUD 画面（World配下で一覧・作成・編集・削除）
- 所有者制限（自分の World/Character のみ管理可能）
- モバイル幅で崩れない最低限スタイルを適用

確認メモ:
- #4（トップページのモバイル可読性）再開条件は満たされている
- M2 の主要Issue（#7, #8, #9, #10, #11, #12）はクローズ済み

## 現在の状況
完了:
- Milestone 1
- Milestone 2

進行中:
- M2-06 完了確認と M3 引き継ぎ

次着手:
- Milestone 3（投稿タイムライン基盤）

## M3 着手タスク（引き継ぎ）
1. Post モデル設計（world / character / author / text / created_at）
2. Character選択付き投稿フォームの実装
3. Worldごとのタイムライン表示（created_at 降順）
4. 投稿一覧のモバイル可読性（1カラム・行間・余白）
5. メンション/返信導線を見据えたURL・テンプレート整理

## 意思決定ログ
- 初回リリースは Milestone 1〜3 に集中する
- タイムライン基盤が安定するまで AI 連携は後ろ倒しにする
- #4 モバイル可読性はテンプレート化後に再評価し、M2 実装で再開条件を満たした
