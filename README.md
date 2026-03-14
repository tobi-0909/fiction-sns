# Fiction SNS

Fiction SNS は、フィクション作品のキャラクターがそれぞれの世界で投稿しているように見える、SNS風タイムラインを目指す実験プロジェクトです。

現在このリポジトリで実装しているのは Django プロトタイプです。長期的には Next.js + TypeScript + PostgreSQL + Prisma の構成を想定しています。

## 現在のスコープ
- 最終ビジョン: AI キャラクター SNS
- 現在の実装範囲: Milestone 1〜3（AI 連携はまだ実施しない）

## クイックスタート（現行 Django プロトタイプ）

1. 仮想環境を作成して有効化（初回のみ）:

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

2. 依存関係をインストール:

```cmd
pip install django
```

3. 開発サーバーを起動:

```cmd
py manage.py runserver
```

4. ブラウザで開く:

- http://127.0.0.1:8000/

## Documentation

- 全体方針とアーキテクチャ: docs/PROJECT_GUIDE.md
- 開発フローとブランチ運用: docs/WORKFLOW.md
- プロダクトロードマップ（既存）: docs/ROADMAP.md
- Milestone / Issue 運用: docs/ISSUE_WORKFLOW.md
- Milestone 計画と Issue 下書き: docs/MILESTONE_PLAN.md, docs/ISSUE_SEEDS.md
- 実行管理ドキュメント（今回追加）: docs/roadmap.md, docs/milestones.md, docs/status.md
