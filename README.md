# fiction-sns

A staged Django project toward an AI character social timeline.

## Why This Repository Exists
This repository is the implementation of early milestones for a larger product vision:
- Final vision: AI Character SNS
- Current scope: milestones up to manual timeline (no AI yet)

## Current Stage
- Environment setup completed (Python, venv, Django)
- Django project and `home` app created
- Root URL connected to `home.index`
- Initial page responds at `/`
- Source is pushed to GitHub

## Project Management Rule
Keep planning and execution explicit in-repo:
- Product direction and long-term path: `docs/roadmap.md`
- Milestone definitions and acceptance criteria: `docs/milestones.md`
- Ongoing progress and next actions: `docs/status.md`

## Immediate Target
Ship milestones 1-3 first:
1. Foundation and basic pages
2. Auth + World/Character CRUD
3. Manual timeline posting

## Development Commands
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate.bat
pip install django
python manage.py runserver
```

## Next Recommended Additions
- Add `.gitignore` for `venv/`, `__pycache__/`, and local DB artifacts if needed
- Add `requirements.txt` once dependencies increase
- Add tests per milestone acceptance criteria
