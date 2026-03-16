# Issue Workflow

This repository uses Issues as the single source of truth for planned work.

## 1. When to create an issue

Create an issue for:

- New feature or behavior change
- Bug fix
- Non-trivial refactor
- Documentation work tied to a milestone

You can skip issue creation for tiny typo-only changes.

## 2. Recommended issue size

A good issue should fit in 1 to 3 commits and be completable in a short session.
If it grows too large, split it.

## 3. Title convention

- Feature: `feat: <short summary>`
- Bug: `fix: <short summary>`
- Task/chore: `chore: <short summary>`

## 4. Lifecycle

1. Open issue
2. Add scope and checklist
3. Implement changes
4. Link commit and/or PR
5. Close issue with a short result note

## 5. Close comment template

Use this when closing an issue:

- What changed:
- Files touched:
- Validation done:
- Follow-up needed:

## 6. Linking commits

Include issue number in commit messages when possible.

Example:

- `feat: add world list page (#12)`
- `fix: handle empty timeline state (#18)`

## 7. Solo development policy

- Small safe changes: direct commit to `main`
- Medium or risky changes: use a branch and optional PR for self-review

The goal is clear history and easy rollback, not process overhead.

---

## 8. Conventions in practice (実際に運用したルール)

このセクションは実装セッションを通じて定着したルールをまとめたもの。

### 8-1. Issue を開く前に仕様を決める

実装を始める前に Issue 本文にスコープ・チェックリスト・除外事項を書く。
特に複数 Issue にまたがる設計判断（例：deny_reason の方針、Follow モデルの仕様）は
**親 Issue や仕様 Issue** を先に立てて決定を記録してから、実装 Issue を開く。

```
- Issue #45: "プロフィールUIの拡張ポイント定義" → 仕様固め専用 Issue
- Issue #44: "Follow モデルとイベントの設計" → 設計判断専用 Issue
```

### 8-2. コメントはライフサイクルの節目に残す

Issue にコメントを残すタイミング：

| タイミング | 内容 |
|---|---|
| 実装前 | スコープ確認・設計判断のメモ |
| 実装中（設計変更時） | 「当初 A を検討したが B に変更した理由」 |
| クローズ時 | Close comment template（セクション 5）に従って記録 |

コメントを残さずにそのままクローズしない。将来の自分や引き継ぎ相手へのドキュメントになる。

加えて、**実装が完了した時点で「何を追加・変更したか」と「なぜその判断にしたか」を必ずコメントで残す**。
クローズコメントに含めてもよいし、実装完了直後に中間コメントとして残してもよい。

最低限、次の 3 点を含める：

- 変更点の要約（モデル / ビュー / テンプレート / テスト）
- 判断理由（採用案と却下案があればその理由）
- 影響範囲（既存仕様への影響、互換性、未対応の課題）

### 8-3. 想定外の仕様変更は新 Issue を切る

実装中に「やっぱりこの動作をもっとよくしたい」と気づいたとき：

- **小さな改善**（元 Issue のスコープ内）: そのままコメントに記録して対応
- **スコープアウト**（別設計判断が必要）: 新しい Issue を立てて元 Issue から参照する

```
例: #39 の 403 固定レスポンスを改善したいと気づいた
→ #52 「アクセス拒否UXのハイブリッド化」を新 Issue として切り出し
→ #39 のクローズコメントに "→ see #52" と記載
```

### 8-4. バックログ Issue は積極的に起票する

「今すぐやらないが将来必要になる」ものは **バックログ Issue** として起票しておく。
ラベル `backlog` を付けて Milestone に紐付けない（または将来の Milestone に紐付ける）。

- 実装中に思いついたアイデアをその場で忘れない
- 次チャット・次セッションで「何が残っているか」が明確になる

### 8-5. Milestone と Issue の紐付け

- Milestone は Goal（段階目標）に一対一で対応させる
- 1 Milestone = 複数の Issue で構成される
- Milestone はすべての Issue がクローズされた後にクローズする
- M3 完了確認用 Issue（#34）のように「まとめ確認 Issue」を最後に置くと抜け漏れを防げる

### 8-6. 大きな変更は先に仕様 Issue に分割する

次のいずれかに当てはまる変更は、実装前に **仕様 Issue / 設計 Issue** を先に立てる：

- 複数ファイル（目安: 4 ファイル以上）へ影響する
- モデル変更・マイグレーションを含む
- 権限・UX・API 応答方針などの振る舞い変更を含む
- 1 セッションで完了しない可能性が高い

実装は「仕様 Issue で合意」→「実装 Issue に分割」の順で進める。
これにより、途中でスコープが膨らんだ場合でも新 Issue へ切り出しやすくなる。

---

## 9. ベストプラクティス提案（他プロジェクトからの知見）

### 9-1. Issue テンプレートを用意する

GitHub の `.github/ISSUE_TEMPLATE/` にテンプレートを置くと、Issue 作成時に自動で雛形が入る。

```markdown
<!-- .github/ISSUE_TEMPLATE/feature.md -->
---
name: Feature
about: 新機能または動作変更
labels: feat
---

## 概要
<!-- 何をするか1〜2行で -->

## スコープ
- [ ] ...
- [ ] ...

## 除外（このIssueではやらないこと）
- ...

## 完了条件
- テストが通る
- マイグレーションが clean
```

### 9-2. ラベルを最初から整備する

最低限このラベルセットを GitHub に作っておくと管理しやすい：

| ラベル | 用途 |
|---|---|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `chore` | メンテナンス |
| `backlog` | 将来対応、優先度低 |
| `blocked` | 依存 Issue 待ち |
| `needs-spec` | 仕様未確定、実装不可 |

ラベルがないと Issue 一覧が増えたときに分類できなくなる。

### 9-3. "決定ログ" コメントを残す

UX や設計で複数案を検討した場合、採用しなかった案とその理由をコメントに残す。

```
検討した案:
- A: 403 を常に返す → バグと区別がつかず混乱しやすい（却下）
- B: 全部リダイレクト → 予期しないエラーまで隠蔽してしまう（却下）
- C: ハイブリッド（想定内=リダイレクト、想定外=403）→ 採用

理由: ユーザーへの可視性と開発者への問題検出のバランスを優先した。
```

これは ADR（Architecture Decision Record）の簡易版として機能する。

### 9-4. Issue と コードをリンクする

実装ファイル内の TODO/FIXME コメントに Issue 番号を付ける：

```python
# TODO(#33): Character bring-in rules — allow members to use their own characters
# FIXME(#19): Edge case when world has no characters
```

こうすると `grep "TODO\|FIXME"` で未解決の技術的負債が一覧できる。

### 9-5. "Done" の定義を Issue ごとに書く

Issue の本文に「完了条件」を明示すると、実装が終わったかどうかの判断が曖昧にならない。

```markdown
## 完了条件
- [ ] /worlds/<id>/post/ が POST リクエストで動作する
- [ ] author/world が正しく保存される
- [ ] ログイン必須（未ログインは 302）
- [ ] 基本テストが pass する
```

チェックリスト形式にすると GitHub UI 上で進捗が可視化される。

### 9-6. クローズ後に関連 Issue を更新する

Issue をクローズしたとき、それに依存している別の Issue のコメントに「#XX 完了」と記録しておく。
次のセッションで「どこから始めればいいか」が即座にわかる。

```
#32 完了（WorldMembership 実装済み）
→ #33（キャラ持ち込みルール）の実装が可能になった
```
