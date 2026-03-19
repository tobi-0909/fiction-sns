# モデレーション・安全運用ガイド

## 概要

本ドキュメントは、fiction-sns における通報・ブロック機能の運用手順と対応フローを定義します。

## 1. ユーザー側の保護機能

### 1.1 ブロック機能

**目的:** 特定ユーザーとの接続を遮断し、嫌がらせや荒らしから保護する。

**ユーザーが実行可能な操作:**
- プロフィールページの「ブロック」ボタンでユーザーをブロック
- 既存のフォロー関係を自動削除
- ブロック中のユーザーをフォロー不可（双方向遮断）
- ブロック中のユーザーの投稿がタイムラインから非表示化

**実装詳細:**
- ブロック先がブロック元をフォロー中の場合も削除される
- ブロック先からのフォローリクエストを受け付けない
- ブロック中ユーザーの投稿を world_timeline で除外フィルタ

### 1.2 通報機能

**目的:** 問題のある投稿・ユーザーを運営に報告し、対応を促す。

**報告対象:**
- **投稿通報**: スパム・虐待・違法コンテンツなど不適切な投稿
- **ユーザー通報**: 継続的な迷惑行為・詐欺行為など

**通報フロー:**
1. ユーザーが投稿 / ユーザー プロフィール上の「通報」リンクをクリック
2. 通報フォームで以下を入力:
   - 通報理由（spam / abuse / nsfw / copyright / other）
   - 詳細説明（オプション）
3. Report モデルに記録（status: OPEN）
4. Django Admin の `ReportAdmin` で管理者が確認・レビュー

### 1.3 レート制限

**投稿 API:**
- 制限: 1ユーザー・1時間あたり最大 **20投稿**
- 超過時: 429 Too Many Requests を返却
- 目的: 自動投稿ツールによるスパム防止

## 2. 運営側の対応フロー

### 2.1 通報対応の優先度

| 優先度 | 内容 | SLA | 対応|
|--------|------|-----|------|
| **Critical** | 違法コンテンツ・児童虐待 | 1時間以内 | 即削除 + 通報者への返信 |
| **High** | 個人情報流出・詐欺 | 4時間以内 | 調査 + 対応 + ユーザー警告 |
| **Medium** | 継続的スパム・ハラスメント | 24時間以内 | 警告 + 必要に応じてブロック |
| **Low** | 軽微な違反・誤報告 | 72時間以内 | 判断 + 適切に対応 |

### 2.2 対応パターン

#### パターンA: 違反投稿への対応
```
1. Admin で Report を "under_review" に変更
2. 投稿を確認・調査
3. 必要に応じて投稿を削除
4. Report status を "resolved" / "dismissed" に更新
5. 通報者への返信（オプション）
```

#### パターンB: 継続的迷惑ユーザーへの対応
```
1. Admin で該当ユーザーの通報複数件を確認
2. ユーザーの history / 投稿内容を調査
3. 警告メッセージを送信（未実装：[#60] で検討）
4. 無視して継続する場合：WorldMembership に kick / ban を適用
5. 必要に応じて: UserBlock を管理者権限で設定
   - 全WorldにおいてユーザーをSilence状態に追加（未実装）
```

### 2.3 Django Admin での操作

**ReportAdmin の画面:**
- List: 全通報を status / reason / created_at でフィルタ・ソート
- Detail: 通報の詳細を確認 → status・reviewed_by を更新

**操作例:**
```
1. Reports → "under_review" フィルタで表示
2. 詳細を確認
3. Status を "resolved" に変更  
4. Save
```

## 3. モデル定義

### Report モデル

```python
class Report(models.Model):
    # 対象タイプ
    target_type: 'post' | 'user'
    
    # 報告者
    reporter: ForeignKey(CustomUser)
    
    # 対象
    target_post: ForeignKey(Post, null=True)
    target_user: ForeignKey(CustomUser, null=True)
    
    # 理由
    reason: 'spam' | 'abuse' | 'nsfw' | 'copyright' | 'other'
    
    # 詳細説明
    description: TextField (optional)
    
    # ステータス
    status: 'open' | 'under_review' | 'resolved' | 'dismissed'
    
    # タイムスタンプ
    created_at: auto_now_add
    reviewed_at: nullable, auto_updated
    reviewed_by: ForeignKey(CustomUser, null=True)
```

### UserBlock モデル

```python
class UserBlock(models.Model):
    blocker: ForeignKey(CustomUser)  # ブロック実行者
    blocked: ForeignKey(CustomUser)  # ブロック対象
    created_at: DateTimeField(auto_now_add=True)
    
    # Constraints:
    # - unique_user_block: (blocker, blocked) 一意
    # - block_no_self_block: blocker != blocked
```

## 4. セキュリティ考慮

### 4.1 通報の機密性
- 通報者は投稿・ユーザー側に非表示（通報者情報は管理者のみ参照可）
- 重複通報は許容（同一ユーザーが同一対象を複数回通報可）

### 4.2 ブロックの可視性
- ブロック状態はプロフィール確認時に「ブロック中」と表示
- ブロック者一覧は管理画面でのみ参照可能

### 4.3 ユーザーへの対応通知
- 現在：対応結果の自動通知なし（後の #60 で検討）
- 推奨：Admin でメッセージ送信機能 or メール通知

## 5. 段階的な公開戦略

### フェーズ1: テスト公開（現在）
- 通報・ブロック機能有効化
- 内部チームでテスト
- Admin での監視・対応

### フェーズ2: 招待制ユーザー公開
- フェーズ1 にて検出された問題を修正
- #60（法務コンプライアンス）実装後
- 50-100 ユーザー規模での段階的展開

### フェーズ3: 完全公開
- #59-#71 全て CLOSED
- SLA 体制構築完了
- 完全公開（招待制解除）

## 6. 将来の拡張（Backlog）

### #70 モデレーション連動タイムライン遮断
- 通報が "resolved" になった投稿をタイムラインから全体的に非表示

### #71 運用 Runbook
- 違法対応手順
- セキュリティインシデント対応
- 24/7 監視体制設計

### 将来検討項目
- 自動スパム検知（ML）
- 段階的 Shadowban（ユーザーには非表示だが投稿は記録）
- コミュニティガイドライン自動チェック

## 7. 参考リンク

- [Report Admin]: `worlds/admin.py` - ReportAdmin
- [UserBlock Admin]: `users/admin.py` - UserBlockAdmin  
- [Leaderboard]: docs/TIMELINE_ARCHITECTURE.md
- [Deploy Guide]: docs/DEPLOY.md
