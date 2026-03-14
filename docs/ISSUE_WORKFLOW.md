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
