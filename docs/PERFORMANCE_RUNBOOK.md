# 性能運用Runbook（タイムライン遅延・DB高負荷）

**最終更新: 2026年3月19日**

**関連ドキュメント:**
- [タイムラインアーキテクチャ](TIMELINE_ARCHITECTURE.md) - 成都背景・設計原則
- [タイムラインSLO](TIMELINE_SLO.md) - 性能基準・計測方法
- [インデックス戦略](TIMELINE_INDEX_STRATEGY.md) - 実測データ
- [カーソル仕様](TIMELINE_FETCH_SPEC.md) - ページング詳細

## 1. 概要

fiction-sns の本番環境で **タイムライン遅延**（応答時間超過）または **DB 高負荷**（CPU/メモリ超過）が発生した場合、運用チームが実施する一次対応フロー を定義します。

### 1.1 対象シナリオ

| シナリオ | 兆候 | 原因想定 | 対応難度 |
|---------|------|--------|--------|
| **タイムライン遅延** | `/worlds/{id}/` のレスポンスが p95=400ms を超過 | N+1 クエリ / インデックス削除 / メモリ不足 | 🟡 中 |
| **DB高負荷 - CPU** | PostgreSQL CPU 使用率 > 80% | 大量同時アクセス / Full table scan | 🔴 高 |
| **DB高負荷 - 接続数** | PostgreSQL conn > 80/100 limit | コネクションプール枯渇 | 🔴 高 |
| **DB高負荷 - メモリ** | PostgreSQL shared_buffers 逼迫 | インデックスキャッシュ未最適化 | 🟡 中 |
| **キャッシュミス多発** | Object cache hit rate < 50% | Redis/Memcached 再起動 / 設定変更 | 🟢 低 |

### 1.2 性能基準（SLO）

```
✅ 正常範囲:
   - p50 応答時間: 100ms 以下
   - p95 応答時間: 400ms 以下
   - p99 応答時間: 1000ms 以下
   - エラー率: < 0.1%
   - 平均クエリ数: 3〜5個（タイムラインGET）
   - 平均クエリ時間: < 100ms

⚠️ 警告範囲:
   - p95 応答時間: 400ms 超過
   - エラー率: 0.1% 超過
   - 平均クエリ数: 8個超過
   - DB CPU: > 70%

🚨 重大範囲:
   - p99 応答時間: 2000ms 超過
   - エラー率: 1% 以上
   - DB接続数: > 90% limit
   - DB メモリ: > 95%
```

---

## 2. 一次対応フロー

### 2.1 症状検出

**検出方法（優先度順）:**

1. **Application Performance Monitoring（APM）**
   - Datadog / New Relic / CloudWatch のダッシュボード確認
   - タイムラインエンドポイント（`GET /worlds/{id}/`）の p95 応答時間
   - 過去 15 分、1 時間、1 日のトレンド確認

2. **ユーザー報告**
   - Slack #support チャネルでの遅延報告
   - エラー報告の件数急増

3. **ログ監視**
   - Application logs の ERROR / WARNING レベル集計
   - 特定エンドポイントのエラー率増加

4. **データベース監視**
   - `SELECT * FROM pg_stat_statements ORDER BY mean_time DESC;`
   - CPU / メモリ / 接続数の推移

---

### 2.2 重大度判定（何の時点でエスカレーション？）

```
【Step 1】初期判定（第一応答者）
└─ p95 > 400ms or エラー率 > 0.1% を検出
   ↓
   │
   ├─ YES → Step 2（診断開始）
   │
   └─ NO → 監視継続（30分ごと確認）

【Step 2】根本原因の初期診断（5分以内）
├─ タイムラインだけ遅い？ ── それ以外も遅い？
├─ DB CPU > 70%？ ─────────── CPU < 70%？
├─ 接続数 > 80？ ──────────── 接続数 < 80？
└─ エラーログに特定パターン？
   ↓
   │
   ├─ 【Acute（急性）】DB 級の問題
   │  ├─ SQL 最悪化（Full table scan）の兆候
   │  ├─ 接続枯渇（> 90/100）
   │  └─ メモリスパイク
   │  → **重大度: CRITICAL** → CTO 報告（電話）
   │
   ├─ 【Chronic（慢性）】アプリ級の問題
   │  ├─ 特定エンドポイントのみ遅い
   │  ├─ N+1 クエリの兆候
   │  └─ 不正なフィルタ条件
   │  → **重大度: HIGH** → DevOps Lead 報告（Slack）
   │
   └─ 【Intermittent（間欠的）】その他
      ├─ キャッシュミス連続
      ├─ GC pause 発生
      └─ ネットワーク遅延
      → **重大度: MEDIUM** → 監視継続（30分）

【Step 3】応急対応（重大度別）
```

---

### 2.3 診断手順（何を見るか？）

#### 📍 診断ポイント 1: Application ログ確認

**コマンド:**
```bash
# Docker logs
docker logs fiction-sns-app --tail 100 | grep -E "ERROR|WARNING|exception"

# または Cloud logs
aws logs tail /aws/ecs/fiction-sns --follow

# または Datadog UI
# → Logs → timeline endpoint → error messages
```

**注目キーワード:**
```
❌ "DatabaseError" ── DB接続失敗
❌ "TimeoutError" ─── クエリタイムアウト
❌ "OperationalError" ─ DB設定エラー
⚠️ "slow query" ────── クエリ遅延
⚠️ "n+1" ──────────── N+1 クエリ検出
```

---

#### 📍 診断ポイント 2: タイムラインクエリ実績確認

**ベンチマーク実行:**
```bash
# 現在のベースラインと比較（開発環境）
python manage.py benchmark_timeline --post-count 200 --runs 20

# 出力例:
# first_page:
#   p50:  150.23 ms
#   p95:  520.45 ms  ← 基準400msを超過 🚨
#   p99:  845.67 ms
# 
# cursor_page:
#   p50:  80.12 ms
#   p95:  200.34 ms ✅
```

**期待値（TIMELINE_INDEX_STRATEGY.md 参照）:**
```
✅ 正常: first_page p95 < 400ms
⚠️  警告: first_page p95 400-800ms
🚨 重大: first_page p95 > 800ms
```

---

#### 📍 診断ポイント 3: DB クエリ分析

**方法 A: Django Debug Toolbar（開発環境）**
```python
# settings.py が DEBUG=True の場合、以下で確認
# http://localhost:8000/worlds/1/?debug=1 (カスタムビュー注: 実装待ち)
# 表示内容:
# - 実行クエリ数（期待値: 3-5個）
# - 各クエリの実行時間
# - N+1 検出（Duplicate queries）
```

**方法 B: pg_stat_statements（本番環境）**
```bash
psql -U fiction_sns -d fiction_sns_prod << 'EOF'
SELECT 
  query,
  calls,
  mean_time,
  max_time
FROM pg_stat_statements
WHERE query LIKE '%world%'
  OR query LIKE '%post%'
  OR query LIKE '%timeline%'
ORDER BY mean_time DESC
LIMIT 10;
EOF

# 出力例:
# query                          | calls | mean_time | max_time
# ─────────────────────────────────────────────────────────
# SELECT ... FROM worlds_post .. |  1521 |  45.23    | 234.11  ← 良好
# SELECT ... FROM users_userb.. |  1521 |   8.12    |  34.56  ← 良好
```

**期待値:**
```
✅ 正常: 平均実行時間 < 100ms
⚠️ 警告: 平均実行時間 100-300ms
🚨 重大: 平均実行時間 > 300ms
```

---

#### 📍 診断ポイント 4: DB リソース確認

**PostgreSQL に接続:**
```bash
psql -U fiction_sns -d fiction_sns_prod

# クエリ確認:
db=# SELECT usename, state, count(*) FROM pg_stat_activity 
     GROUP BY usename, state;
     
# 出力例:
# usename | state   | count
# ─────────────────────────
# fiction | active  |    8   ← 接続活発（許容範囲内）
# fiction | idle    |   12   ← アイドル接続
# postgres| active  |    1

# 詳細確認:
db=# SELECT pid, usename, application_name, state, wait_event FROM pg_stat_activity 
     WHERE state != 'idle'
     ORDER BY query_start DESC;

# 実行時間が長いクエリを特定:
db=# SELECT pid, usename, query, now() - query_start as duration
     FROM pg_stat_activity
     WHERE state != 'idle'
     ORDER BY duration DESC;
```

**期待値:**
```
✅ 正常:
   - 接続数 < 70/100 limit
   - active query < 5個
   - 単一クエリ実行時間 < 1000ms

⚠️ 警告:
   - 接続数 70-85/100
   - active query 5-10個
   - 単一クエリ実行時間 1-5秒

🚨 重大:
   - 接続数 > 90/100
   - active query > 10個
   - 単一クエリが 10秒以上ブロック
```

---

#### 📍 診断ポイント 5: インデックス状態確認

**現在の有効インデックス:**
```bash
psql -U fiction_sns -d fiction_sns_prod

db=# SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
     FROM pg_stat_user_indexes
     WHERE schemaname = 'public'
     ORDER BY idx_scan DESC;

# 出力例:
# schemaname | tablename | indexname                     | idx_scan  | idx_tup_read | idx_tup_fetch
# ──────────────────────────────────────────────────────────────────────────────────
# public     | worlds_post | idx_post_world_timeline     | 234521    | 45232100     | 45231900 ✅
# public     | users_follow | idx_following_list         | 123456    | 23451200     | 23451100 ✅
# public     | worlds_post | idx_post_author_recent      | 45123     | 8923100      | 8923000  ✅
# public     | worlds_report | idx_report_status_time    | 1234      | 234567       | 234500   ✅
```

**チェック項目:**
```
✅ idx_post_world_timeline の idx_scan が多い → インデックス活用中
❌ idx_post_world_timeline の idx_scan が少ない → インデックス無視の可能性
❌ idx_tup_read > idx_tup_fetch が大きい → フルスキャン兆候
```

---

### 2.4 即座対応（何をするか？）

#### 🔧 対応 1: キャッシュクリア（10分）

**シナリオ**: 間欠的な遅延、キャッシュ更新直後

```bash
# Django キャッシュクリア
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> print("Cache cleared")

# または Redis キャッシュ
redis-cli FLUSHALL

# または特定キーのみクリア
redis-cli DEL "fiction:timeline:*"
```

**期待効果:**
- ✅ キャッシュミスが原因なら即座に改善
- ⚠️ それ以外の原因なら効果なし（次へ）

---

#### 🔧 対応 2: Query 最適化ヒント（若干）

**シナリオ**: N+1 クエリの兆候、特定ユーザー向けフィルタ問題

**worlds/views.py の world_timeline() を確認:**

```python
# 現在の実装:
base_posts = (
    Post.objects.filter(world=world, author__is_active=True)
    .select_related('character', 'author')  # ✅ 既に最適化
    .order_by('-created_at', '-id')
)

# ブロック除外（⚠️ 毎回クエリ走る - キャッシュ対象）:
if request.user.is_authenticated:
    from users.models import UserBlock
    blocked_user_ids = UserBlock.objects.filter(
        blocker=request.user
    ).values_list('blocked_id', flat=True)  # ← ここで追加クエリ
    base_posts = base_posts.exclude(author_id__in=blocked_user_ids)
```

**一次対応の処置:**

❌ **これはするな**: `exclude()` を `query()` に変更（複雑化）

✅ **これをする**: 別の施策が効くか確認

---

#### 🔧 対応 3: トラフィック制限（即効性高）

**シナリオ**: DB CPU > 80%、接続枯渇

```bash
# Nginx / ALB のレート制限を引き上げる
# （または降ろす・タイムアウト短縮）

# または Django 側での一時的制限:
RATELIMIT_ENABLE = True  # .env に設定
RATELIMIT_GET_TIMELINE = "10/m"  # 1分10リクエスト(通常20/h)

# または特定ユーザーを一時遮断（#71対応）
```

**復旧手順:**
```bash
# 30分後に解除
RATELIMIT_GET_TIMELINE = "20/h"  # 元に戻す
```

---

#### 🔧 対応 4: Graceful Degradation（段階的機能削減）

**シナリオ**: DB がほぼダウン状態（接続 > 95%）

```python
# Django middleware で自動実施（実装:詳細は下記記事参照）

# 一時的に機能削減:
FEATURE_FLAGS = {
    'timeline_with_relations': False,  # キャラクター情報非表示
    'timeline_with_recommendations': False,  # おすすめ非表示
    'block_exclude': False,  # ブロック除外スキップ（極端）
}
```

**効果:**
- タイムライン基本情報のみ返却
- DB クエリが 40% 削減
- ユーザーは「簡易版表示」として認識

---

### 2.5 エスカレーション基準

#### レベル 1: 監視継続（30分）

**条件:**
- p95 < 600ms
- エラー率 < 0.5%
- DB CPU < 80%

**対応:**
```
[ DevOps on call ] が以下をモニタ:
- 2024-11-15 14:00 - 14:30: ダッシュボード監視
- 15分ごとにベンチマークテスト実行
- 30分後に改善判定

報告: Slack #ops-alerts に定期update（10分ごと）
```

---

#### レベル 2: HIGH - DevOps Lead へ報告

**条件:**
- 600ms < p95 < 1000ms
- 0.5% < エラー率 < 2%
- DB CPU 80-90%
- 対応 1-3 で改善しない

**対応:**
```
[ DevOps Lead ] に Slack で報告:
@devops-lead #ops-alerts
---
🔴 HIGH: Timeline response p95=720ms (threshold 400ms)
Error rate: 1.2%
DB CPU: 85%
Applied: cache clear, rate limit reduction
Status: 問題継続中

次ステップ: Query profiling 開始
---

DevOps Lead の判定:
  A. DB 再起動（予測不可ダウンリスク）
  B. Read-only レプリカへの切替
  C. 緊急デプロイ（修正コード）
```

**SLA: 15分以内に対応開始**

---

#### レベル 3: CRITICAL - CTO へ報告（電話）

**条件:**
- p99 > 2000ms
- エラー率 > 5%
- DB接続 > 95/100
- DB メモリ > 95%
- 対応 1-4 で改善なし

**対応:**
```
[ DevOps on call ] が CTO に電話:
  "タイムライン CRITICAL。DB ほぼダウン状態。
   接続数 98/100。メモリ 97%。
   キャッシュクリア・レート制限応用済み。
   Graceful degradation 検討。"

CTO の判定:
  A. 全トラフィック遮断（緊急保護）
  B. DB 強制再起動（ユーザーセッション喪失リスク）
  C. Regional failover（複数拠点構成の場合）
  D. Customer communication（ユーザーアナウンス）
```

**SLA: 5分以内対応開始、10分以内に状況改善**

---

## 3. 記録・監査・エスカレーション

### 3.1 対応記録の保存場所

**主要チャネル:**

| 記録先 | 用途 | アクセス権 |
|--------|------|----------|
| **Slack #ops-alerts** | リアルタイム update | ops team |
| **CloudWatch Logs** | Application log archive | DevOps |
| **pg_stat_statements テーブル** | クエリ実績 | DBA / DevOps |
| **Jira INCIDENT** | 振り返り・改善追跡 | 全関連者 |
| **Datadog APM** | メトリクス保存 | DevOps / SRE |
| **Incident.io** | インシデント管理（Phase 2） | 全関連者 |

---

### 3.2 対応記録テンプレート

**Jira Issue 作成（Incident type）:**

```
件名: [INCIDENT] Timeline p95 > 400ms on 2026-03-19 14:15

説明:
---
## 発生時刻
2026-03-19 14:15 UTC

## 検出方法
CloudWatch dashboard alert

## 症状
- Endpoint: GET /worlds/{id}/
- p95 response: 720ms （基準: 400ms）
- Error rate: 1.2%
- Duration: 45分

## 根本原因
idx_post_world_timeline インデックスが pg_stat_statements で無視される兆候
→ Query planner が Full table scan を選択した可能性

## 実施した対応
[時刻] Cache clear
[時刻] Rate limit reduction (20/h → 10/m)
[時刻] Query profiling

## 結果
→ p95: 720ms → 520ms (改善)
→ 対応2時間後、正常復帰

## 対応者
@devops-lead, @dba-team

## 関連ドキュメント
- [TIMELINE_INDEX_STRATEGY.md](TIMELINE_INDEX_STRATEGY.md)
- [PERFORMANCE_RUNBOOK.md](PERFORMANCE_RUNBOOK.md)

## Follow-up
- [ ] インデックスヒント追加（PostgreSQL 15+）
- [ ] ブロック除外のメモリキャッシュ化（#72）
- [ ] Automated query warning（pg_stat_statements 監視）
---
```

---

### 3.3 振り返り会（Incident review）

**対象**: CRITICAL / HIGH レベルのインシデント

**タイミング**: 解決後 1 営業日以内

**参加者**: DevOps Lead, CTO, DBA (if applicable), Dev team lead

**議題:**
1. タイムライン（何が起きたか、いつ解決したか）
2. 根本原因（なぜ起きたか）
3. 対応の妥当性（やったことは正しかったか）
4. 再発防止策（何を改善するか）
5. ドキュメント更新（Runbook に追記？）

**成果物:**
- Jira に改善 ticket を作成
- Runbook 更新（新パターン発見時）
- Team knowledge share（Slack thread に記録）

---

## 4. メンテナンス・改善計画

### 4.1 定期監視（SLA維持）

| リズム | 実施内容 | 責任者 |
|--------|---------|--------|
| **毎日** | CloudWatch dashboard 確認（5分） | DevOps on call |
| **毎週** | pg_stat_statements slow query review（30分） | DBA / DevOps |
| **毎月** | Runbook 更新（新パターン、改善反映） | DevOps Lead |
| **四半期** | 本番性能ベンチマーク（POST 数×3倍データで計測） | DevOps + Dev |

---

### 4.2 既知の改善見込み機構（Phase 2 候補）

| 改善 | 見込み効果 | 難度 | 優先度 |
|-----|----------|------|--------|
| ブロック除外のメモリキャッシュ | クエリ数-20% | 🟡 低 | 🔴 高 |
| Prefetch_related 最適化 | クエリ時間-30% | 🟢 低 | 🔴 高 |
| Redis 導入 | レスポンス-40% | 🟠 中 | 🟡 中 |
| Pull first → Push タイムライン移行 | スケール到達時点 | 🔴 高 | 🟡 中 |
| Read-only レプリカ分散 | 多重度×2-3 | 🔴 高 | 🟢 低 |

---

## 5. トラブルシューティング FAQs

### Q1: "p95 が突然 800ms になった。何から始める？"

**A:** 以下の順で診断:
1. **応用ログを 5 行見る** （ERROR/WARNING あるか）
2. **ベンチマーク実行** （再現性があるか）
3. **pg_stat_statements で遅いクエリを特定** （どのテーブル？）
4. **EXPLAIN ANALYZE** で実行計画確認 （インデックス使用？）

**時間: 5-10分で根本原因見つかる見込み**

---

### Q2: "インデックスが削除されてしまった。復旧方法は？"

**A:** マイグレーションで再作成:
```bash
# 誤削除の場合は reverse
python manage.py migrate worlds 0006

# 再適用
python manage.py migrate worlds
```

**事前防止:**
```bash
# インデックス存在確認を CI に組み込む
python manage.py check_indexes  # カスタムコマンド（実装待ち）
```

---

### Q3: "DB接続数が 95/100 になった。即座の対応は？"

**A:** 以下を順に実行:
```bash
# Step 1: アイドル接続を閉じる
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
          WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"

# Step 2: Django connection pool リセット
python manage.py flush --no-input  # 本番では使用禁止！

# Step 3: Django アプリを cyclic restart
# (Kubernetes/Docker を使用している場合)
kubectl rollout restart deployment/fiction-sns-app

# Step 4: それでも > 90 の場合は CTO 報告（エスカレーション Level 3）
```

---

### Q4: "特定 World のタイムラインだけ遅い"

**A:** World 固有の問題の可能性:
```bash
# その World の投稿数を確認
psql -c "SELECT COUNT(*) FROM worlds_post WHERE world_id = 123;"

# インデックスカバレッジを確認
psql -c "EXPLAIN ANALYZE SELECT * FROM worlds_post 
         WHERE world_id = 123 ORDER BY created_at DESC LIMIT 20;"

# ブロック中のユーザーが多い可能性（exclude が重い）
psql -c "SELECT COUNT(*) FROM users_userblock WHERE blocker_id = 456;"
```

**対応:**
- 投稿数 > 10万の World →　read-only レプリカへ専用化（Phase 2）
- ブロック数 > 1000 のユーザー → メモリキャッシュ対象化（#72）

---

### Q5: "エラーログに 'slow query' が出ている。どのクエリ？"

**A:** pg_slow_log を確認:
```bash
# postgresql.conf で設定
log_min_duration_statement = 1000  # 1秒以上のみログ

# ログ確認
tail -f /var/log/postgresql/postgresql.log | grep "duration"
```

**期待値:**
- タイムライン GET: 平均 < 100ms
- タイムライン cursor: 平均 < 80ms

---

## 6. 改定履歴

| 版 | 日付 | 変更 |
|----|------|------|
| 1.0 | 2026-03-19 | 初版（Issue #71 サポート） |

---

**最後の更新者**: DevOps チーム
**次回レビュー予定**: 2026-06-19
