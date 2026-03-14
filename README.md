# Fiction SNS

Fiction SNS is an experimental project for a social timeline app where fictional characters post as if they are living in their own worlds.

Current implementation in this repository is a Django prototype. The long-term target stack is Next.js + TypeScript + PostgreSQL + Prisma.

## Current Scope
- Final vision: AI Character SNS
- Current implementation scope: milestones 1 to 3 (no AI integration yet)

## Quick Start (Current Django Prototype)

1. Create and activate virtual environment (first time only):

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

2. Install dependencies:

```cmd
pip install django
```

3. Run development server:

```cmd
py manage.py runserver
```

4. Open:

- http://127.0.0.1:8000/

## Documentation

- Project direction and architecture: docs/PROJECT_GUIDE.md
- Development workflow and branch policy: docs/WORKFLOW.md
- Product roadmap (existing): docs/ROADMAP.md
- Milestone and issue operations: docs/ISSUE_WORKFLOW.md
- Milestone plan and issue seeds: docs/MILESTONE_PLAN.md, docs/ISSUE_SEEDS.md
- Working execution docs (new): docs/roadmap.md, docs/milestones.md, docs/status.md
