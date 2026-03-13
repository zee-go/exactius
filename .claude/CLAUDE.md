# Exactius — Multi-Account Meta Ads Automation Platform

Automated campaign creation for Meta Ads Manager from Google Drive assets.
Manages multiple client ad accounts from a single platform.

## Purpose

Agency-focused Meta Ads automation: Google Drive link → assets uploaded → campaigns
created. Handles multi-account credential management, custom naming rules per client,
and campaign audit trails.

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, facebook-business SDK, Facebook Marketing API v19.0
- **Frontend**: Next.js (App Router), TypeScript, Zustand, Tailwind CSS
- **Cloud**: Google Secret Manager (credentials), Google Drive API (assets)
- **Infra**: Docker (Dockerfile.backend, frontend/Dockerfile.frontend)

## Architecture

```
frontend/          # Next.js app (dashboard, campaign wizard, history)
src/
  api/             # FastAPI app — routes, models, dependencies
  accounts/        # Multi-account management
  assets/          # Asset validation (images, videos)
  campaigns/       # Campaign/adset/ad/creative managers
  drive/           # Google Drive client + URL parser
  naming/          # Client-specific naming convention resolver
  orchestrator/    # Campaign launcher (end-to-end orchestration)
  reporting/       # Analytics
  secrets/         # Google Secret Manager integration
  utils/           # retry.py — exponential backoff decorator
  main.py          # CLI entry point
  config.py        # Config + env vars
  auth.py          # Meta API authentication
```

## Key Patterns

- **Auth**: Long-lived Meta tokens stored in Google Secret Manager (not .env in prod)
- **Rate limiting**: `@with_retry` decorator in `src/utils/retry.py` handles Meta API codes 4, 17, 32, 341, 613
- **Async uploads**: `ThreadPoolExecutor` (4 workers) for parallel asset uploads
- **Naming**: Per-client naming rules in `src/naming/` with custom overrides

## Commands

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload   # API server at localhost:8000

# Frontend
cd frontend && npm install && npm run dev   # Dev server at localhost:3000

# Testing
pytest tests/                              # 79 tests, all passing
python src/main.py --help                  # CLI interface

# Containers
docker build -f Dockerfile.backend -t exactius-api .
docker build -f frontend/Dockerfile.frontend -t exactius-frontend ./frontend
```

## Environment Variables

Required (local dev only — prod uses Secret Manager):
- `FB_ACCESS_TOKEN` - Meta Marketing API access token
- `FB_APP_ID` / `FB_APP_SECRET` - Meta App credentials
- `FB_AD_ACCOUNT_ID` - Target ad account (format: act_123456789)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON
- `NEXT_PUBLIC_API_KEY` - API key for frontend → backend auth

Optional:
- `FB_API_VERSION` - API version (defaults to v19.0)
- `LOG_LEVEL` - Logging level (defaults to INFO)

## Getting Started

See `docs/facebook-api-setup.md` for Meta API setup and `docs/google-secret-manager-setup.md`
for Secret Manager configuration. Run `gcloud auth application-default login` before
starting (required for Secret Manager access in local dev).

## Guardrails

- IMPORTANT: Verify before creating/launching campaigns (real money at stake)
- IMPORTANT: Never modify live campaigns without explicit approval
- Always test with small budgets first; confirm targeting and creative before launch

## Session Memory

Uses `docs/active.md` (task tracker) + `docs/decisions.md` (decision log).
Read active.md at session start to surface due/overdue tasks.

## Reference Documents (on-demand)

- `docs/active.md` — task tracker (read every session)
- `docs/decisions.md` — append-only decision log
- `docs/projects.md` — project registry if managing multiple ad accounts
- `docs/facebook-api-setup.md` — Meta API setup and authentication guide
- `docs/google-secret-manager-setup.md` — Secret Manager setup guide
- `docs/automation-rules.md` — automation workflow documentation
