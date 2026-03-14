# Fiction SNS Project Guide

## 1. Goal

Build a timeline-focused fiction SNS where characters in a fictional world generate and publish posts.

## 2. Current State

- Runtime in this repository: Django prototype
- Root route (`/`) is connected to the `home` app
- Current top page response: `Fictions flow SNS（仮）`

## 3. Product Direction

### Long-term product image

- Timeline UI focused reading experience
- Creator defines `World` and `Character`
- AI generates in-world posts
- Readers move across multiple timelines (world / following / discover)

### Short-term MVP

- Manage `World`
- Manage `Character`
- Show `Post` list per `World`
- Keep flows small and testable

## 4. Canonical Domain Terms

Use these names consistently across all prototypes and future implementations:

- `World`
- `Character`
- `Post`
- `User`
- `CitizenContribution`
- `ReadProgress`

Avoid alternative names like Story, Universe, or Project for the same concept.

## 5. Target Stack (Long-term)

- Frontend: Next.js (App Router) + TypeScript
- Backend: Next.js Route Handlers / Server Actions / API Routes
- Database: PostgreSQL + Prisma
- Deployment:
  - During development: local or Docker
  - Future candidates: Vercel + Supabase / Railway

## 6. Migration Note

The current Django code should be treated as a prototype for validating product flows and domain design.

When moving to Next.js:

- Reuse domain terms, route design, and product requirements
- Expect app code (views, routing, ORM, templates) to be rewritten
- Keep implementation modular to reduce migration cost

## 7. Web-first Mobile Strategy

Recommended strategy for this project size (solo development):

1. Build a responsive web app first
2. Keep API/data model stable and UI responsibilities clear
3. Consider PWA as the first mobile step
4. Build native app later only if push/device integration needs become strong
