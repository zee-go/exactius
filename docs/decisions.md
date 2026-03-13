# Decision Log

> Reverse-chronological record of significant decisions. Captures the "why" so
> future sessions don't re-litigate settled questions.
> Append new entries at the top.

## 2026-03-13 — Testing: Mock-based Unit Tests (no integration tests yet)

- **Decided**: Unit tests only for now, all external dependencies mocked. No integration
  tests against real Meta API or Google Cloud.
- **Why**: Integration tests require live credentials (gcloud auth, Meta tokens) which
  aren't set up yet. Mock-based tests validate all pure logic paths — URL parsing, asset
  validation, naming templates, retry backoff — without external dependencies. Integration
  tests can be added once credentials are in place.

## 2026-03-13 — Docker: Separate Dockerfiles per service (not docker-compose yet)

- **Decided**: `Dockerfile.backend` at project root, `frontend/Dockerfile.frontend` in
  frontend dir. No docker-compose file yet.
- **Why**: Each service deploys independently to Cloud Run. docker-compose is useful for
  local dev orchestration but not required for the deployment target. Can add
  `docker-compose.yml` later when local full-stack dev becomes a priority.

## 2026-03-13 — API Authentication: Optional API Key (X-API-Key Header)

- **Decided**: Use a simple `X-API-Key` header enforced globally via FastAPI dependency.
  Skip auth entirely when `API_KEY` env var is not set (dev mode).
- **Why**: Low overhead for an internal tool. No user login needed — single shared key
  is sufficient. Dev-safe default (no key = no block) avoids friction during local testing.
  Can upgrade to JWT or OAuth later if the platform becomes multi-user.

## 2026-03-13 — Retry Strategy: Decorator with Exponential Backoff

- **Decided**: `@with_retry()` decorator in `src/utils/retry.py`, applied per-method on
  manager classes. Retries on FB rate limit codes (4, 17, 32, 341, 613) and transient
  errors (1, 2). Default: 4 retries, 2s base, 60s cap.
- **Why**: Decorator approach keeps each manager method self-contained and testable.
  Exponential backoff respects Facebook's rate limit windows. Non-retriable errors
  (validation, auth) surface immediately — no wasted retries.

## 2026-03-13 — Asset Upload: Parallel with ThreadPoolExecutor

- **Decided**: Replace sequential asset upload loop with `ThreadPoolExecutor(max_workers=4)`.
- **Why**: Each asset upload is I/O-bound (HTTP to Meta). Sequential was the bottleneck —
  10 images took ~30s. 4 concurrent workers brings this to ~8-10s. Cap at 4 to stay within
  Meta's per-token rate limits. Failures on individual assets remain isolated.

## 2026-03-13 — Frontend Wizard State: Zustand (not URL params or React state)

- **Decided**: Zustand store for wizard step state. History persisted via Zustand `persist`
  middleware to `localStorage`.
- **Why**: Wizard spans 5 steps with shared state that needs to survive step navigation.
  URL params would expose Drive URLs and context in the browser bar. React context would
  require provider wrapping. Zustand is already a project dependency and gives clean
  reset/persist APIs without boilerplate.

## 2026-02-10 — Initial Architecture: Python + Facebook Business SDK

- **Decided**: Use Python with the official facebook-business SDK for campaign
  automation, rather than direct REST API calls or other language options.
- **Why**: Python has the most mature and well-maintained Facebook SDK, excellent
  data processing libraries for analytics, and is ideal for automation scripts.
  The official SDK handles API versioning, authentication, and error handling better
  than manual REST calls.
- **See**: `.claude/CLAUDE.md` for tech stack details

## 2026-02-10 — Project Structure: Full Orchestrator Model

- **Decided**: Implement the full operating model structure with .claude/, docs/,
  rules/, and persistent memory patterns from the start.
- **Why**: Starting with the complete structure enables better session continuity,
  task tracking, and decision logging from day one. Easier to set up now than
  retrofit later. Supports scaling to multiple ad accounts or child projects.
