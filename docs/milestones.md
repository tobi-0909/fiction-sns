# Milestones（実行計画）

この文書は、Roadmap の目標を実装可能なチェックポイントへ落とし込むためのものです。

## Milestone 1（1〜2週）
スコープ:
- ローカル Django プロジェクトが起動する
- ブラウザでシンプルなトップページが表示できる
- リポジトリ初期化と push が完了している

受け入れ条件:
- python manage.py runserver がエラーなく起動する
- GET / でカスタムページが返る
- 初期コミット後に git status が clean である

## Milestone 2（2〜4週）
スコープ:
- Django 標準認証による登録・ログイン・ログアウト
- World の CRUD
- Character の CRUD（World と関連付け）
- モバイル向け最低限レイアウト調整

データモデル草案:
- World: title, description, created_at, owner
- Character: world, name, profile, personality, created_at

受け入れ条件:
- 認証フローが一通り動作する
- ログインユーザーが自身の World/Character を作成・編集できる
- 狭い画面幅でもフォームが利用可能である

## Milestone 3（3〜6週）
スコープ:
- Post モデル
- Character 選択付き投稿 UI
- World タイムライン（新しい順）

データモデル草案:
- Post: world, character, text, created_at, author

受け入れ条件:
- Character を選んで投稿できる
- タイムラインが created_at の降順で表示される
- モバイルで 1 カラム表示として読みやすい

## Milestone 4（M3 後に 2〜3週）
スコープ:
- マネージドホスティングへデプロイ
- 外部ネットワークからスマホアクセス確認

受け入れ条件:
- 公開 URL が利用可能
- スマホブラウザで一連の操作が通る

## 任意 Milestone 5〜6（後続）
- AI 投稿生成
- 投稿範囲の AI 要約
- 読了位置記録またはフォロー状態保持

## リスクメモ
- Milestone 間でのスコープ膨張
- スキーマ安定前に AI 実装を始めること
- CRUD エンドポイントの所有者チェック漏れ
