# Decision Log

> Reverse-chronological record of significant decisions. Captures the "why" so
> future sessions don't re-litigate settled questions.
> Append new entries at the top.

## 2026-07-08 — ClickUp → Meta video sync via status-based webhook

- **Decided**: Automate downloading video attachments from ClickUp and uploading
  them to the Meta Ad Library using (1) direct ClickUp REST calls with a personal
  API token — no ClickUp MCP dependency, and (2) the existing `facebook-business`
  SDK / ad account token — no new Meta App or App Review. Trigger is a ClickUp
  `taskStatusUpdated` webhook: when a task reaches the configured status
  (`CLICKUP_TRIGGER_STATUS`, default "ready for ads"), its videos sync automatically.
- **Why**: The user explicitly required a workaround that avoids MCP and a new Meta
  App. Uploading to `/{ad-account-id}/advideos` only needs `ads_management`, which
  the platform already has. Status-based triggering gives editors control over which
  videos reach Meta (only approved ones) and is event-driven, avoiding polling lag.
- **Account selection (multi-account)**: The target Meta ad account is chosen
  **per task** via a ClickUp custom dropdown field named "Meta Ad Account"
  (configurable via `CLICKUP_ACCOUNT_FIELD`). The selected option's label is the
  account short name ("nike") or ad account ID ("act_123"), resolved through
  `AccountManager`. If no account is selected, the task is **skipped with a warning**
  (`NoAccountSelectedError`) — nothing is uploaded to a wrong account. This replaced
  the earlier list→account map so editors can target different accounts from the same
  list. The ClickUp token in multi-account mode comes from
  `exactius-shared-clickup-api-token`. Single-account mode reads everything from
  `.env` and ignores the field (one account only).
  Use `scripts/list_clickup_fields.py` to verify the field/options are set up.
- **Notes**: ClickUp attachment URLs are pre-signed S3 links — fetched WITHOUT the
  ClickUp auth header (S3 rejects dual auth). `FacebookAdsApi.init()` must be called
  before uploading (CreativeManager does not self-init — mirrors CampaignLauncher).
  Webhooks are HMAC-SHA256 verified via `CLICKUP_WEBHOOK_SECRET`.
- **See**: `src/clickup/` (client, parser, resolver),
  `src/orchestrator/clickup_sync.py`, `src/api/routes/clickup.py`,
  `scripts/register_clickup_webhook.py`, `tests/test_clickup_*.py`

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
