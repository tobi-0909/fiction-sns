# Development Workflow

## 1. Solo Development Rule

For this project stage, speed and clarity are more important than strict process.

## 2. Branch Strategy

### Recommendation

Use this lightweight branch model:

- `main`: always runnable state
- `feature/<topic>`: for non-trivial changes
- `fix/<topic>`: for bug fixes
- `docs/<topic>`: for documentation updates

### Do you always need a branch?

No. In solo development, branch creation is optional for very small and low-risk edits.

Create a branch when at least one condition is true:

- Change touches multiple files
- Data model/migration changes are included
- You are not sure the implementation direction is stable
- You may need to discard work safely

For tiny docs typo fixes or very small safe edits, direct commit to `main` is acceptable.

## 3. Commit Convention

Prefer small and meaningful commits.

Example prefixes:

- `feat:` new feature
- `fix:` bug fix
- `refactor:` code cleanup without behavior change
- `docs:` documentation only
- `chore:` maintenance

## 4. Pull Request Usage (Optional for Solo)

Even as a solo developer, PRs can be useful as review checkpoints for medium/large changes.

Suggested rule:

- Small changes: direct commit to `main`
- Medium/large changes: branch + PR + merge

## 5. VS Code Daily Loop

1. Pull latest code
2. Start server and verify baseline behavior
3. Implement one small scoped change
4. Run local checks
5. Commit with clear message
6. Push backup to GitHub
