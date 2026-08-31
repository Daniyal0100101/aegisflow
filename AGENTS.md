# AGENTS.md

## Project Purpose

AegisFlow is Daniyal's independent, public-safe multi-agent operational decision simulation platform. It is the current derivative/product lane that came after the private Learnify Health evaluation, but it must remain distinct from Learnify materials.

## Durable Project Context

Read these AGENT_OS docs before non-trivial work:

- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/PROJECT_INDEX.md`
- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/PRD.md`
- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/ARCHITECTURE.md`
- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/UI_SPEC.md`
- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/TASKS.md`
- `/mnt/c/Users/DANIYAL/Documents/Ideaverse/AGENT_OS/01_PROJECTS/aegisflow/DECISIONS.md`

## Repo Layout

```
multiagent-sim/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js 15 dashboard
├── packages/
│   ├── agents/       # agent roles, scenarios, domain configs
│   ├── evaluation/   # confidence scoring and safety grading
│   ├── orchestration/ # workflow graph engine + Gemini SDK integration
│   ├── shared_types/ # Pydantic backend models
│   └── state_engine/ # deterministic state transition rules
├── docs/app-demo.png
├── Makefile
├── docker-compose.yml
└── README.md
```

Workflow graph pipeline:
1. `CONTEXT_PREP`
2. `PROPOSAL_GENERATION`
3. `CRITIC_REVIEW`
4. `RESOLVE_CONSENSUS`
5. `STATE_MUTATION`
6. `COMMIT_LOGS`

See `PROJECT_INDEX.md` and inspect the repo before editing. Do not assume structure from memory.

## Commands

### Python Backend
- `cd apps/api && python -m unittest discover -s packages -p '*_test.py'`
- `cd apps/api && python -m pytest` (if pytest configured)
- `docker compose up --build api`

### Frontend
- `cd apps/web && npm run dev`
- `cd apps/web && npm run build`
- `cd apps/web && npm run lint`
- `cd apps/web && npm run typecheck`

### Full Stack
- `docker compose up --build`
- `make test` (runs all validation)

## Coding Conventions

Match existing code and dependencies. Keep changes scoped and simple. Do not introduce new libraries or abstractions without a project need.

### Python (FastAPI)
- Type hints required on public functions
- Pydantic models for request/response
- Dependency injection via FastAPI `Depends`

### TypeScript/Next.js
- App Router patterns
- Server components by default
- UI components in `components/`

## Testing Expectations

Run the narrowest relevant command from this repo before claiming completion. Prefer build/typecheck/lint/test scripts already defined in `package.json` or project docs.

### Validation Snapshot (2026-07-09)
- Private identifier scan: passed — no Learnify/Mahdi/Jelodari/NDA/Demo Day/old Learnify repo identifiers found in source/docs
- Python backend/unit tests: passed via `.venv/bin/python -m unittest discover -s packages -p '*_test.py'`
- Frontend build: passed via `npm run build --prefix apps/web`
- Frontend lint/typecheck scripts: no-op/pass via `npm run lint --if-present --prefix apps/web` and `npm run --if-present typecheck --prefix apps/web`
- Dependency audit: passed via `npm audit --prefix apps/web --audit-level=moderate` with `found 0 vulnerabilities`

Dependency-audit note: earlier warning came from Next's transitive `postcss@8.4.31`; fix updated Next/React package floors and added explicit `postcss@8.5.16` npm override because `npm audit fix --force` proposed an unsafe breaking downgrade.

## Deployment Notes

No production deployment configured yet. Local development via `docker compose up` or individual service commands. Ask before deployment or external publication.

## Forbidden Actions

- Do not read `.env`, tokens, OAuth files, or credentials unless explicitly asked.
- Do not commit, push, deploy, publish, or contact external services without approval.
- Do not start unrelated refactors or feature expansion from context-maintenance tasks.
- Do not copy exact Learnify repo/materials/prompts/screenshots/docs into AegisFlow.
- Keep AegisFlow branded and documented as Daniyal's own generalized operational simulation platform.

## Relationship To Learnify

- Learnify Health Evaluation remains a private reference-only project at `../learnify-health-evaluation/`.
- AegisFlow is the independent public-safe lane.
- Do not copy exact Learnify repo/materials/prompts/screenshots/docs into AegisFlow.