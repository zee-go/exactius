# ClickUp → Meta Video Sync — Setup Guide (Multi-Account)

Automatically upload video attachments from ClickUp tasks to the correct Meta
ad account's Media Library when a task reaches a chosen status. The account is
picked **per task** via a ClickUp dropdown field.

No ClickUp MCP and no new Meta App are required — this uses direct ClickUp REST
and the existing `facebook-business` SDK / per-account tokens.

---

## How it works

```
Editor sets "Meta Ad Account" dropdown on a task  ─┐
Editor moves task to "Ready for Ads"               ─┤
                                                    ▼
ClickUp fires taskStatusUpdated webhook  →  POST /api/clickup/webhook
                                                    ▼
  verify HMAC signature → status == trigger? → read dropdown → resolve account
                                                    ▼
  download video (pre-signed S3 URL) → FacebookAdsApi.init → upload to /act_XXX/advideos
                                                    ▼
                          Meta video ID (ready for an ad creative)
```

If a task has **no account selected**, it is skipped and a warning is logged —
nothing is uploaded to a wrong account.

---

## Prerequisites

- Multi-account mode is active (`GOOGLE_CLOUD_PROJECT` set; accounts in Secret
  Manager as `exactius-accounts-*`, per `docs/google-secret-manager-setup.md`).
- The API service is deployed at a public HTTPS URL (Cloud Run).
- A ClickUp **personal API token** (`pk_...`) with access to the relevant lists.

---

## Step 1 — Store the ClickUp token + set config

**Secret Manager** (used by the running service in multi-account mode):

```bash
printf '%s' 'pk_XXXXXXXX' | gcloud secrets create exactius-shared-clickup-api-token \
  --data-file=- --project="$GOOGLE_CLOUD_PROJECT"
```

**Environment variables** on the API service:

| Variable | Required | Default | Notes |
|---|---|---|---|
| `CLICKUP_WEBHOOK_SECRET` | yes | — | Random string; also passed at webhook registration. Enables HMAC verification. |
| `CLICKUP_TRIGGER_STATUS` | no | `ready for ads` | ClickUp status (lower-cased) that triggers a sync. Must match your status name exactly. |
| `CLICKUP_ACCOUNT_FIELD` | no | `Meta Ad Account` | Name of the ClickUp dropdown field that selects the account. |
| `CLICKUP_API_TOKEN` | no | — | Only for local/single-account dev. In production the token comes from the secret above. |

Generate a webhook secret: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## Step 2 — Create the "Meta Ad Account" dropdown in ClickUp

1. On the ClickUp list (or Space, so it applies to all its lists), add a **custom
   field** of type **Dropdown** named exactly **`Meta Ad Account`**
   (or whatever you set `CLICKUP_ACCOUNT_FIELD` to).
2. Add one **option per account**, labelling each option with that account's
   **short name** (e.g. `nike`, `adidas`) or its **ad account ID**
   (e.g. `act_123456789`). The label must match an account known to
   `AccountManager` (i.e. the `account_name` or `account_id` in its
   `exactius-accounts-*-config` secret).

Verify the field name and option labels line up:

```bash
CLICKUP_API_TOKEN=pk_XXXX python scripts/list_clickup_fields.py --list-id <LIST_ID>
```

The output lists each dropdown option — the labels shown here are exactly what the
sync will look up as an account identifier.

---

## Step 3 — Register the webhook

```bash
CLICKUP_API_TOKEN=pk_XXXX python scripts/register_clickup_webhook.py \
  --team-id <TEAM_ID> \
  --endpoint https://<your-service-url>/api/clickup/webhook \
  --secret "$CLICKUP_WEBHOOK_SECRET"
```

- `TEAM_ID` is the workspace ID in your ClickUp URL: `app.clickup.com/<TEAM_ID>/…`
- The `--secret` **must equal** the service's `CLICKUP_WEBHOOK_SECRET`, or every
  webhook will be rejected with 401.

The script prints the webhook ID (save it — it's how you'd delete the webhook later).

---

## Step 4 — Test end-to-end

1. On a task with a video attachment, set **Meta Ad Account** = one of your accounts.
2. Move the task to **Ready for Ads**.
3. Watch the service logs — you should see:
   `Task <id> reached 'ready for ads' — queuing video sync`, then
   `Synced '<file>' → Meta video ID <id>`.
4. Confirm the video appears in that account's Meta **Media Library**.

**Manual trigger** (bypasses the webhook, explicit credentials — handy for a first test):

```bash
curl -X POST https://<your-service-url>/api/clickup/sync-videos \
  -H "Content-Type: application/json" \
  -d '{"task_id":"<TASK_ID>","ad_account_id":"act_123","access_token":"<TOKEN>"}'
```

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Webhook returns 401 | `--secret` at registration ≠ service `CLICKUP_WEBHOOK_SECRET`. |
| Nothing happens on status change | Status name ≠ `CLICKUP_TRIGGER_STATUS` (case/spacing), or webhook not registered for `taskStatusUpdated`. |
| Log: "has no 'Meta Ad Account' selected — skipping" | The task's dropdown is empty. |
| Log: "Selected account '…' could not be loaded" | Dropdown option label doesn't match any account short name / ID in Secret Manager. |
| Download fails | ClickUp token lacks access to the task, or the attachment isn't a supported video type (mp4, mov, avi, wmv, webm). |
| Upload fails / auth error | Account's Meta token expired, or shared `app_id`/`app_secret` missing. |

---

## Reference

- Code: `src/clickup/` (client, parser, resolver), `src/orchestrator/clickup_sync.py`,
  `src/api/routes/clickup.py`
- Scripts: `scripts/register_clickup_webhook.py`, `scripts/list_clickup_fields.py`
- Decision: see `docs/decisions.md` (2026-07-08 entry)
