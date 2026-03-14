# Roadmap

This document tracks long-term product direction.

## Product Vision
Create an AI Character SNS where users can build fictional worlds and characters, publish timeline posts, and optionally use AI features (generation or summarization).

## Stage Goals

### Goal 0: Environment Setup
- Python + Django local setup works
- GitHub repository initialized and synced

### Goal 1: Auth + World/Character Management
- User sign-up/login/logout
- Create/edit World from mobile browser
- Create/edit Character linked to World

### Goal 2: Manual Timeline
- Timeline per World
- Post as selected Character
- Mobile-friendly scrolling timeline

### Goal 3: First AI Integration
Implement one of:
- Character post generation
- Story summary generation

### Goal 4: User State Persistence
Implement one of:
- Follow World feature
- Read position tracking

### Goal 5+: Progressive AI and UX Expansion
- Deeper prompt quality
- Better timeline UX
- Operational hardening

## Sequencing Principle
Do not start Goal 3 until Goals 1-2 have stable data models and basic tests.

## Definition of "Milestone Done"
A milestone is done only when:
- Feature works on desktop and mobile browser
- Migration state is clean
- Basic tests pass
- Documentation is updated in `docs/status.md`
