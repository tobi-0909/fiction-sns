# Issue Seeds

This file contains ready-to-create issues for each milestone.

## Milestone 1: Environment Setup + Hello World Django

Target duration: 1 to 2 weeks

### M1-01: chore: set up local Python environment and venv

Labels:
- chore

Body:

Background:
Prepare a reproducible local Python environment for Django development.

Task:
- Install Python 3 if not present
- Create virtual environment
- Activate virtual environment
- Verify pip is available

Acceptance Criteria:
- [ ] Python version is confirmed
- [ ] venv exists in project workspace
- [ ] pip can install package in active venv
- [ ] Basic setup steps are documented in README

Definition of Done:
- [ ] Commands were tested on local machine
- [ ] No unrelated files changed

### M1-02: feat: bootstrap Django project and verify runserver

Labels:
- enhancement

Body:

Summary:
Initialize Django project and verify local server startup.

Goal / User Value:
Project can be run at any time from local environment.

Scope:
In scope:
- django-admin startproject
- runserver on localhost
Out of scope:
- production deployment

Tasks:
- [ ] Install Django in venv
- [ ] Verify manage.py exists and works
- [ ] Start runserver and confirm default page

Definition of Done:
- [ ] Local startup command works repeatedly
- [ ] Root URL is reachable on localhost
- [ ] Steps are documented in README

### M1-03: feat: add home app and custom top page

Labels:
- enhancement

Body:

Summary:
Add home app and replace default page with project top page.

Goal / User Value:
Confirm basic routing and first app integration.

Scope:
In scope:
- home app creation
- root URL mapping
- simple top page response
Out of scope:
- authentication
- DB models

Tasks:
- [ ] Create home app
- [ ] Add app to INSTALLED_APPS
- [ ] Add home urls and project include
- [ ] Implement top page response

Definition of Done:
- [ ] Opening root path displays custom page
- [ ] URL routing is minimal and clear
- [ ] No 404/500 on root

### M1-04: chore: make top page mobile-friendly baseline

Labels:
- chore

Body:

Background:
Project direction is web-first with smartphone readability.

Task:
- Add template-based top page
- Add viewport meta
- Add minimum CSS so layout does not break on narrow width

Acceptance Criteria:
- [ ] Top page readable on mobile width
- [ ] Buttons/links are tappable size
- [ ] No horizontal overflow at common widths

### M1-05: chore: initialize repository workflow and docs

Labels:
- chore

Body:

Background:
Keep implementation history understandable from early stage.

Task:
- Ensure README exists and points to docs
- Keep workflow guide and roadmap visible
- Confirm issue templates are available

Acceptance Criteria:
- [ ] README links to docs
- [ ] Workflow document exists
- [ ] Roadmap document exists
- [ ] Issue templates are selectable on GitHub

### M1-06: chore: milestone-1 completion checklist and closeout note

Labels:
- chore

Body:

Background:
Record what was achieved and prepare next milestone transition.

Task:
- Validate M1 behavior end-to-end
- Capture screenshots or short notes
- Write closeout summary for M1

Acceptance Criteria:
- [ ] Local server starts cleanly
- [ ] Custom top page is shown
- [ ] Smartphone browser check completed
- [ ] Transition notes for M2 are documented

---

## Operating Rule for New Issues

For work discovered during implementation:

- Open a new issue immediately when task is larger than tiny typo fix
- Link commit message with issue number when possible
- Close issue with a short result note

Close note template:

- What changed:
- Files touched:
- Validation done:
- Follow-up needed:
