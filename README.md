# fiction-sns

フィクション世界のキャラクターがタイムラインに投稿する、創作特化の SNS プロトタイプです。
Django で実装した段階的なリリースプロジェクトです。

## 現在の状態（2026-03-24）

Milestone 4 の主要機能が完成し、本番公開準備フェーズにあります。

**完成済み機能:**
- ユーザー認証（登録・ログイン・ログアウト）
- World / Character の CRUD
- キャラクターによるタイムライン投稿（カーソルページング付き）
- World の公開/非公開制御とアクセス管理（kick / ban / 監査ログ）
- 公開プロフィール・フォロー / フォロワー一覧
- フォロー機能（鍵アカウント対応の承認フロー）
- ブロック・通報機能
- レート制限（投稿 20件 / 時間）
- TOS・プライバシーポリシーページ

**進行中:**
- 本番インフラ準備（PostgreSQL 移行・HTTPS 設定・CI）
- #58 タイムライン性能ガード設計

**保留・将来方針:**
- Milestone 5（AI 独り言生成）→ 採算と受容性が整った段階で再検討
- 長期的なスタック移行（Next.js / PostgreSQL）は `docs/PROJECT_GUIDE.md` 参照

詳細な進捗は `docs/status.md` を参照してください。

## プロジェクト管理方針

計画と実行をリポジトリ内で明示的に管理します。
- プロダクト方向・長期方針: `docs/roadmap.md`
- マイルストーン定義と受け入れ条件: `docs/milestones.md`
- 現在の進捗と次アクション: `docs/status.md`

## ローカル開発手順

```bash
python -m venv venv
source venv/bin/activate  # Windows の場合: venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## テスト実行

```bash
# 全テスト（80件）
python manage.py test

# アプリ別に実行
python manage.py test worlds users

# 本番設定チェック
python manage.py check --deploy
```

## 主要ドキュメント

| ドキュメント | 内容 |
|---|---|
| `docs/DEPLOY.md` | 本番デプロイ手順（Render 対応） |
| `docs/E2E_TEST.md` | スマホ実機 E2E 検証シナリオ |
| `docs/MODERATION.md` | 通報・ブロック運用ガイド |
| `docs/PERFORMANCE_RUNBOOK.md` | タイムライン遅延時の対応手順 |
| `docs/TIMELINE_SLO.md` | 性能基準と計測方法 |
