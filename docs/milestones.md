# Milestones (Execution Plan)

This document converts roadmap goals into implementable checkpoints.

## Milestone 1 (Week 1-2)
Scope:
- Local Django project running
- Simple top page available from browser
- Repository initialized and pushed

Acceptance Criteria:
- `python manage.py runserver` starts without errors
- `GET /` returns custom page
- `git status` clean after initial commit

## Milestone 2 (Week 2-4)
Scope:
- Django auth for sign-up/login/logout
- World CRUD
- Character CRUD (linked to World)
- Basic mobile layout improvements

Data Model Draft:
- World: `title`, `description`, `created_at`, `owner`
- Character: `world`, `name`, `profile`, `personality`, `created_at`

Acceptance Criteria:
- Auth flow works end-to-end
- Logged-in user can create/edit own World and Character
- Forms are usable on narrow screens

## Milestone 3 (Week 3-6)
Scope:
- Post model
- Character-based posting UI
- World timeline page sorted by newest first

Data Model Draft:
- Post: `world`, `character`, `text`, `created_at`, `author`

Acceptance Criteria:
- User can create post with selected Character
- Timeline shows posts in descending `created_at`
- Mobile timeline is readable in one-column layout

## Milestone 4 (Week 2-3 after M3)
Scope:
- Deploy to managed hosting
- Confirm smartphone access from external network

Acceptance Criteria:
- Public URL available
- Full user flow works on phone browser

## Optional Milestone 5-6 (Later)
- AI post generation
- AI summary of timeline range
- Read progress or follow-state persistence

## Risk Notes
- Scope creep between milestones
- Starting AI too early before schema stabilizes
- Missing ownership checks in CRUD endpoints
