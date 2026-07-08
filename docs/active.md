# Active Tasks & Reminders

> This file is the source of truth for what's in-flight, what needs checking,
> and what's coming up. Claude reads this at the start of every session and
> surfaces anything due or overdue. Update at the end of every session.

---

## In Progress

- **[TBD] Google Cloud Authentication** — Need to run `gcloud auth application-default login`
  to authenticate for Secret Manager access. Auth token expired, requires interactive login.
  Next: Run authentication command in terminal.

- **[TBD] Secret Manager Setup** — Configure Google Secret Manager with Meta credentials
  and account configurations. Next: Follow guide in docs/google-secret-manager-setup.md.
  Requires: gcloud authentication, Secret Manager API enabled.

- **[TBD] Meta Ads API Setup** — Create Meta App, get Marketing API access, generate
  long-lived access tokens for each client account. Next: Follow setup guide in
  docs/facebook-api-setup.md.

## Pending Review

- **[2026-07-08] ClickUp → Meta video sync** — Built the full pipeline (client,
  parser, credential resolver, sync worker, webhook + manual routes, registration
  script, 18 passing tests). Single- and multi-account modes supported. Next: deploy,
  register the webhook (`scripts/register_clickup_webhook.py`), set `CLICKUP_*` env /
  secrets, and run one real end-to-end task through "Ready for Ads". For multi-account,
  populate the `exactius-shared-clickup-account-map` secret.

## Scheduled Checks

_(No scheduled checks yet)_

## Completed (Recent)

- ~~[2026-02-10] Project evolution to multi-account platform~~ — Upgraded from single-account
  to multi-account Meta Ads automation platform. Added FastAPI backend, Google Secret Manager
  integration, multi-account management, comprehensive API with endpoints for account operations.
  Updated requirements.txt with all dependencies (FastAPI, Google Cloud libraries, asset
  processing tools). Created comprehensive documentation including Secret Manager setup guide.

- ~~[2026-02-10] Google Cloud SDK installed~~ — Installed and upgraded gcloud CLI to
  version 556.0.0. Configured for project agent-486219 with account zee@resourcematch.ph.
  Ready for Secret Manager API enablement after authentication.

- ~~[2026-02-10] Initial project structure created~~ — Set up orchestrator-style
  directory structure with .claude/, docs/, rules/, src/. Created CLAUDE.md,
  session protocols, and documentation files.

---

## How This File Works

**Sections:**
- **In Progress** — actively being worked on across sessions
- **Pending Review** — done but needs verification after a time delay
  (date = when to check)
- **Scheduled Checks** — recurring or future reviews (date = when due)
- **Completed (Recent)** — finished items, kept for ~30 days then removed

**Rules:**
- Dates in brackets are due dates, not start dates
- Move items down as they progress: In Progress -> Pending Review -> Completed
- Remove completed items older than 30 days (they're in git history)
- If an item spawns new work, add the new item and complete the original
