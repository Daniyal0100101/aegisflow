# AegisFlow UI_SPEC

Last updated: 2026-07-22

## Purpose

Defines the user-facing behavior, layout, and interaction patterns for the AegisFlow dashboard. This is the implementation reference for the Next.js 15 web app in `apps/web/`.

---

## Layout Structure

### App Shell (`app/layout.tsx`)

- Single-page layout with persistent header and main content area
- No sidebar; navigation via domain selector in header
- Global CSS reset in `app/globals.css` (vanilla CSS, no Tailwind)

### Header

- **App title**: "AegisFlow"
- **Domain selector**: Dropdown with three options — Clinical Triage, Disaster Response, Supply Chain / Logistics
- **Mode indicator**: Sandbox (no API key) vs Live (Gemini key present)
- **Session controls**: New Session button, Session ID display

### Main Content — Two Panels (Desktop) / Stacked (Mobile)

#### Left Panel: Workflow Graph (`WorkflowGraph.tsx`)

Visual representation of the 6-step pipeline:

1. `CONTEXT_PREP`
2. `PROPOSAL_GENERATION`
3. `CRITIC_REVIEW`
4. `RESOLVE_CONSENSUS`
5. `STATE_MUTATION`
6. `COMMIT_LOGS`

- Each step shows: status (pending/running/complete/error), timing, agent count
- Clicking a step reveals the log events for that step in the right panel
- Animated transitions between states (CSS keyframes)

#### Right Panel: Log & Metrics

**Top: Metrics Panel (`MetricsPanel.tsx`)**

- Domain-specific KPIs (e.g., patient vitals, evacuation progress, port throughput)
- Confidence/safety scores from critic review
- Real-time updates during simulation

**Bottom: Log Event Feed (`LogEventItem.tsx`)**

- Chronological event stream from `COMMIT_LOGS`
- Each entry: timestamp, step, agent/role, action, outcome, confidence
- Color-coded lozenges: `inprogress` (blue), `success` (green), `removed` (red), `warning` (amber)
- Expandable details for each event

### Override Panel (`OverridePanel.tsx`)

- Floating/fixed panel accessible from any step
- Human-in-the-loop controls:
  - Accept proposal as-is
  - Modify proposal (free-text override)
  - Reject and force re-generation
  - Emergency stop (halts simulation)
- Override actions are logged with `actor: "human"` in audit trail

---

## Interaction Flows

### 1. New Session

1. User selects domain from header dropdown
2. Clicks "New Session"
3. POST `/session/start` with `{ domain }`
4. Response: `{ session_id, initial_state }`
5. UI initializes workflow graph at `CONTEXT_PREP`, metrics at baseline

### 2. Step Execution (Auto-Advance)

1. Frontend polls `/session/{id}/events` (or SSE if implemented)
2. Each step completes → graph node updates → metrics update → log events append
3. On `CRITIC_REVIEW` complete: show confidence scores, enable Override Panel
4. On `STATE_MUTATION` complete: metrics reflect new state
5. On `COMMIT_LOGS` complete: session marked complete; final summary shown

### 3. Human Override

1. User opens Override Panel at any step (enabled after `PROPOSAL_GENERATION`)
2. Selects action: Accept / Modify / Reject / Stop
3. If Modify: free-text input for revised command
4. POST `/session/{id}/override` with `{ action, revision? }`
5. Engine re-runs from `RESOLVE_CONSENSUS` with human input
6. Override logged; graph shows "human" actor badge

### 4. Sandbox vs Live Mode

- **Sandbox** (default, no `GEMINI_API_KEY`): deterministic mock responses from `packages/orchestration/engine.py` fallback
- **Live** (`GEMINI_API_KEY` set): real Gemini 3 Flash calls via `google-genai` SDK
- Mode badge in header reflects current state
- No UI difference except response quality/latency

---

## Components Reference

| Component | File | Props | Notes |
|-----------|------|-------|-------|
| `WorkflowGraph` | `components/WorkflowGraph.tsx` | `steps: Step[]`, `activeStep: number`, `onStepClick: (idx) => void` | SVG-based or CSS-grid; 6 fixed nodes |
| `MetricsPanel` | `components/MetricsPanel.tsx` | `domain: Domain`, `metrics: MetricSnapshot` | Domain-specific render via switch |
| `LogEventItem` | `components/LogEventItem.tsx` | `event: LogEvent`, `expanded: boolean`, `onToggle: () => void` | Recursive for nested details |
| `OverridePanel` | `components/OverridePanel.tsx` | `sessionId: string`, `disabled: boolean`, `onOverride: (action) => void` | Portal-rendered to body |
| `DomainSelector` | `components/DomainSelector.tsx` | `value: Domain`, `onChange: (d) => void` | Header dropdown |
| `ModeBadge` | `components/ModeBadge.tsx` | `mode: 'sandbox' \| 'live'` | Header indicator |

---

## Data Contracts (Frontend ↔ Backend)

### Session Start Response

```ts
interface SessionStartResponse {
  session_id: string;
  domain: Domain;
  initial_state: DomainState;
  mode: 'sandbox' | 'live';
}
```

### Domain State (per domain)

```ts
interface DomainState {
  // Clinical Triage
  patient?: { vitals: Vitals; condition: string; history: string[] };
  // Disaster Response
  incident?: { type: string; severity: number; affected_zones: string[] };
  // Supply Chain
  port?: { throughput: number; backlog: number; cyber_status: 'ok' | 'degraded' | 'down' };
  // Common
  step: WorkflowStep;
  timestamp: string;
}
```

### Log Event

```ts
interface LogEvent {
  step: WorkflowStep;
  agent: string;        // e.g., "cardiologist", "critic", "human"
  action: string;
  outcome: 'success' | 'partial' | 'failure' | 'pending';
  confidence?: number;  // 0-1 from critic
  duration_ms: number;
  timestamp: string;
  details?: Record<string, unknown>;
}
```

### Metric Snapshot

```ts
interface MetricSnapshot {
  domain: Domain;
  primary: { label: string; value: number | string; trend?: 'up' | 'down' | 'flat' }[];
  secondary: { label: string; value: number | string }[];
  confidence: number;      // 0-1 aggregate
  safety_score: number;    // 0-1 from critic
}
```

---

## Styling & Theming

- Vanilla CSS in `app/globals.css` — CSS variables for colors, spacing
- No Tailwind, no CSS-in-JS
- Color tokens:
  - `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
  - `--fg-primary`, `--fg-secondary`, `--fg-muted`
  - `--accent-blue`, `--accent-green`, `--accent-amber`, `--accent-red`
  - `--border-subtle`, `--border-strong`
  - `--radius-sm`, `--radius-md`, `--radius-lg`
- Dark mode via `prefers-color-scheme` media query
- Component-scoped CSS Modules where needed (e.g., `WorkflowGraph.module.css`)

---

## Accessibility

- Semantic HTML: `<header>`, `<main>`, `<section>`, `<nav>`
- ARIA labels on all interactive controls
- Focus-visible outlines on all focusable elements
- Live region for log feed updates (`aria-live="polite"`)
- Color contrast ≥ 4.5:1 in both themes
- Keyboard navigation: Tab through graph nodes, panel controls, override actions

---

## Responsive Breakpoints

- **≥ 1024px**: Two-panel layout (graph left, logs/metrics right)
- **768px–1023px**: Stacked; graph collapsible accordion above logs
- **< 768px**: Single column; header condenses; override panel becomes full-screen modal

---

## Error & Empty States

| State | UI Treatment |
|-------|--------------|
| No session started | Centered "Start a simulation" card with domain selector |
| API error (5xx) | Toast + inline banner; "Retry" button re-runs last step |
| Network offline | Banner "Offline — changes will sync when reconnected" |
| Empty log feed | "No events yet. Start a session to begin." |
| Sandbox mode warning | Subtle badge: "Running in sandbox — connect GEMINI_API_KEY for live AI" |

---

## Commands (Dev)

```bash
# From multiagent-sim root
npm run dev --prefix apps/web          # Next.js dev server (port 3000)
npm run build --prefix apps/web        # Production build
npm run lint --prefix apps/web         # ESLint (if configured)
docker compose up --build              # Full stack (API + Web)
```

---

## Linked AGENT_OS Docs

- `PROJECT_INDEX.md` — project status, repo paths, validation snapshots
- `PRD.md` — product framing, domains, scope boundaries
- `ARCHITECTURE.md` — system overview, engine packages, workflow graph
- `RUNBOOK.md` — operational commands, deployment, troubleshooting
- `DECISIONS.md` — durable choices (stack, sandbox fallback, no auth, etc.)
- `RISKS.md` — known risks (clinical claims, sandbox fidelity, etc.)
- `CHANGELOG.md` — version history

---

## Notes for Implementers

1. **Do not add auth, multi-tenancy, or persistence** — explicitly out of scope per PRD
2. **Keep sandbox deterministic** — mock responses must be reproducible for demos
3. **Override panel is the safety differentiator** — prioritize its usability
4. **Domain metrics are mock data** — no real sensors; generate plausible values
5. **WebSocket/SSE not implemented** — polling is fine for demo-scale sessions
6. **No analytics, tracking, or external scripts** — keep it self-contained