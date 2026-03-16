# デプロイガイド（M4-13）

本文書は、fiction-sns を公開環境へデプロイするための手順と注意事項をまとめたものです。

## 1. デプロイ前の確認

### 1-1. ローカル環境でのチェック
本番環境への前に、ローカルで本番同等の設定でテストします：

```bash
# 本番設定をシミュレート
DEBUG=False python manage.py check --deploy

# 静的ファイルの集約テスト
python manage.py collectstatic --noinput

# テスト実行
python manage.py test worlds users
```

### 1-2. チェックリスト
- [ ] `DEBUG=False` で起動エラーがないこと
- [ ] 静的ファイル（CSS）が正しく collectstatic で集約されること
- [ ] すべてのテストが成功すること（テスト数: 33+件）

## 2. 本番環境設定

### 2-1. 環境変数（.env）の準備
本番環境では以下を設定します：

```
# 必須設定
DEBUG=False
SECRET_KEY=<本番用の安全なSECRET_KEY（python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' で生成）>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2-2. セキュリティ設定
Django チェックリスト（`python manage.py check --deploy`）で以下を確認：

- [ ] `DEBUG=False`（ローカルでのみ True を許可）
- [ ] `ALLOWED_HOSTS` が明示的に設定されている
- [ ] `SECRET_KEY` が本番用の強いキーである
- [ ] `CSRF_TRUSTED_ORIGINS` が正しく設定されている

## 3. デプロイ手順（サンプル: Render.com）

### 3-1. Render へのデプロイ
Render（またはRailway, Heroku 等）を使用する場合の一般的な手順：

1. **リポジトリをGitHubに push**
   ```bash
   git push origin main
   ```

2. **Render.com でプロジェクト新規作成**
   - New + Web Service
   - GitHub repo を接続
   - runtime: Python 3.10

3. **環境変数を設定**
   - Render のダッシュボード → Environment
   - 以下を追加：
     - `DEBUG=False`
     - `SECRET_KEY=<生成したキー>`
     - `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
     - `CSRF_TRUSTED_ORIGINS=https://yourdomain.com,...`

4. **ビルドコマンド**
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```

5. **スタートコマンド**
   ```bash
   gunicorn fiction_sns.wsgi:application --bind 0.0.0.0:$PORT
   ```

6. **デプロイ実行**
   - Deploy ボタンをクリック

### 3-2. 本番環境URL
デプロイ完了後、Render が割り当てた URL（例: `https://fiction-sns-xyz.onrender.com`）で主要ページにアクセス可能。

## 4. 公開URL確認テスト

### 4-1. アクセス検証
本番環境の公開URL に対して以下を確認：

- [ ] トップページ（/）が 200 で返る
- [ ] ログインページ（/auth/login/）が 200 で返る
- [ ] 新規登録ページ（/auth/signup/）が 200 で返る
- [ ] CSS が読み込まれている（スタイルが反映）

### 4-2. 機能テスト
実際の操作フロー（#75 E2E検証）で以下を検証：

- [ ] ユーザー登録ができる
- [ ] ログイン → World 一覧が見える
- [ ] World 作成ができる
- [ ] タイムラインが表示される（投稿一覧）

## 5. トラブルシューティング

### DisallowedHost エラーが出る場合
- ALLOWED_HOSTS に公開URL のドメイン が含まれているか確認
- 設定後、デプロイを再実行

### 静的ファイル（CSS）が読み込まれない場合
- `python manage.py collectstatic --noinput` が成功したか確認
- STATIC_ROOT が正しく指定されているか確認（docs/settings.py の STATIC_ROOT を確認）

### データベース接続エラーが出る場合
- 本番環境が SQLite（ローカルDB）を使用している場合、各デプロイ環境は再起動時に DB をリセット
- 本番環境では PostgreSQL 等の外部DB への切り替えを検討

## 6. 本番環境への段階的移行

### 6-1. 初期公開時
- ローカルユーザー数 <10
- 内部テスト + 関係者のみ
- 毎日トレース・エラーログを確認

### 6-2. 段階的拡大
- ユーザー数 <100: β版として公開
- ユーザー数 <500: 本番環境安定性確認（#71 Runbook 着手）
- ユーザー数 500+: Pull first → Push 型への移行判定（#72）

## 7. 関連Issue・リンク
- #74: デプロイ基盤実装（本Issue）
- #75: スマホ実機E2E検証
- #58: タイムライン性能ガード設計
- #67: タイムライン最低性能SLO
- #71: 障害時運用Runbook

## 8. 参考リンク
- Django Deployment Checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Render Python Guide: https://render.com/docs/deploy-django
- Gunicorn: https://gunicorn.org/
