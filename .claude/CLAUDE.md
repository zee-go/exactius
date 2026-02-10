# Exactius — Facebook Ads Automation Platform

Automated campaign management and optimization for Facebook Ads Manager. Handles
campaign creation, budget adjustments, performance monitoring, and reporting.

## Purpose

Programmatic Facebook Ads campaign automation using the Facebook Marketing API.
Reduces manual campaign management overhead and enables data-driven optimization
at scale.

## Tech Stack

- **Runtime**: Python 3.12+
- **SDK**: facebook-business (official Meta SDK)
- **API**: Facebook Marketing API v19.0
- **Storage**: TBD (Firestore, PostgreSQL, or file-based initially)

## Architecture

```
src/
  main.py              # Entry point
  config.py            # Configuration and environment variables
  auth.py              # Facebook API authentication
  campaigns/           # Campaign management modules
  reporting/           # Analytics and reporting
  automation/          # Automation workflows and rules
```

## Key Patterns

- **Authentication**: Uses long-lived access tokens stored in environment or secrets
- **Rate limiting**: Facebook API has rate limits - implement backoff/retry logic
- **Error handling**: Facebook API errors are verbose - log and handle gracefully
- **Async operations**: Many Facebook API operations are async - poll for completion

## Commands

```bash
# Development
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run automation
python src/main.py

# Testing
pytest tests/
```

## Environment Variables

Required:
- `FB_ACCESS_TOKEN` - Facebook Marketing API access token
- `FB_APP_ID` - Facebook App ID
- `FB_APP_SECRET` - Facebook App Secret
- `FB_AD_ACCOUNT_ID` - Target ad account ID (format: act_123456789)

Optional:
- `FB_API_VERSION` - API version (defaults to v19.0)
- `LOG_LEVEL` - Logging level (defaults to INFO)

## Getting Started

1. Create a Facebook App at https://developers.facebook.com
2. Get Marketing API access (requires business verification)
3. Generate access token with ads_management permissions
4. Set environment variables in `.env` file
5. Run `python src/main.py --help` for available commands

See `docs/facebook-api-setup.md` for detailed setup instructions.

## Guardrails

- IMPORTANT: Verify before creating/launching campaigns (real money at stake)
- IMPORTANT: Never modify live campaigns without explicit approval
- Always test with small budgets first
- Confirm targeting and creative before launch
- Monitor spend limits to prevent budget overruns

## Session Memory

Uses `docs/active.md` (task tracker) + `docs/decisions.md` (decision log).
Read active.md at session start to surface due/overdue tasks.

## Reference Documents (on-demand)

- `docs/active.md` — task tracker (read every session)
- `docs/decisions.md` — append-only decision log
- `docs/projects.md` — project registry if managing multiple ad accounts
- `docs/facebook-api-setup.md` — API setup and authentication guide
- `docs/automation-rules.md` — automation workflow documentation
