# Exactius — Multi-Account Meta Ads Automation Platform

Automated campaign creation and management for Meta Ads Manager (Facebook/Instagram ads), designed for **agencies managing multiple client accounts**.

## Overview

Exactius is a web application that automates the creation of Meta ad campaigns from Google Drive assets. Key features:

- 🏢 **Multi-Account Management**: Manage multiple client ad accounts from one platform
- 🔐 **Secure Credential Storage**: Google Secret Manager for centralized credential management
- 🎯 **Custom Naming Rules**: Client-specific naming conventions per campaign type
- 📁 **Google Drive Integration**: Share Drive link → Assets automatically uploaded to Meta
- 🚀 **FastAPI Backend**: Modern, async Python backend with REST API
- 📊 **Campaign Tracking**: Audit trail and campaign history

## Architecture

```
Next.js Frontend (Coming Soon)
        ↓
FastAPI Backend (Python)
        ↓
   ┌─────────┬─────────────┬──────────┐
   │  Secret │   Google    │   Meta   │
   │ Manager │  Drive API  │ Ads API  │
   └─────────┴─────────────┴──────────┘
```

**Current Status**: ✅ Backend Phase 1 Complete
- Secret Manager integration
- Account management
- API routes for account operations
- Multi-account support

**Next Steps**:
- Google Drive integration
- Meta API campaign creation
- Frontend development

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured
- Meta Business Manager access
- Meta app with Marketing API access

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd exactius

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

#### Option A: Multi-Account Mode (Recommended for Production)

Uses Google Secret Manager for secure credential storage.

```bash
# Copy and edit .env
cp .env.example .env

# Edit .env and set:
# GOOGLE_CLOUD_PROJECT=your-project-id

# Authenticate with Google Cloud
gcloud auth application-default login
```

**Set up Secret Manager**: Follow the comprehensive guide at [docs/google-secret-manager-setup.md](docs/google-secret-manager-setup.md)

#### Option B: Single-Account Mode (Local Development)

For testing with a single ad account using local `.env` file.

```bash
# Edit .env and uncomment/fill in:
# FB_ACCESS_TOKEN=your_token
# FB_APP_ID=your_app_id
# FB_APP_SECRET=your_app_secret
# FB_AD_ACCOUNT_ID=act_123456789
```

### 3. Verify Setup

Test Secret Manager integration:

```bash
python scripts/test_secret_manager.py
```

This will verify:
- ✓ Secret Manager connection
- ✓ Account configurations
- ✓ Credential access
- ✓ Configuration validity

### 4. Start API Server

```bash
# Using helper script
./scripts/start_api.sh

# Or directly
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test API

Open your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Or use curl:

```bash
# List all accounts
curl http://localhost:8000/api/accounts/

# Get account details
curl http://localhost:8000/api/accounts/nike

# Validate account access
curl http://localhost:8000/api/accounts/nike/validate

# Get available campaign types
curl http://localhost:8000/api/accounts/nike/campaign-types
```

## Project Structure

```
exactius/
├── .claude/                    # Claude Code configuration
│   ├── CLAUDE.md               # Project context
│   └── rules/                  # Session protocols
├── docs/                       # Documentation
│   ├── active.md               # Task tracker
│   ├── decisions.md            # Decision log
│   ├── google-secret-manager-setup.md  # Secret Manager guide
│   └── facebook-api-setup.md   # Meta API setup guide
├── src/                        # Source code
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── dependencies.py     # Dependency injection
│   │   ├── routes/             # API route modules
│   │   │   └── accounts.py     # Account endpoints
│   │   └── models/             # Pydantic models
│   │       ├── accounts.py     # Account schemas
│   │       └── campaigns.py    # Campaign schemas
│   ├── secrets/                # Google Secret Manager
│   │   └── manager.py          # Secret Manager client
│   ├── accounts/               # Account management
│   │   └── manager.py          # Account operations
│   ├── config.py               # Configuration management
│   ├── auth.py                 # Meta API authentication
│   ├── campaigns/              # Campaign management (coming soon)
│   ├── reporting/              # Analytics and reporting (coming soon)
│   └── automation/             # Automation rules engine (coming soon)
├── scripts/                    # Utility scripts
│   ├── test_secret_manager.py  # Test Secret Manager setup
│   └── start_api.sh            # Start API server
├── tests/                      # Tests
└── requirements.txt            # Python dependencies
```

## API Endpoints

### Accounts

- `GET /api/accounts/` - List all configured accounts
- `GET /api/accounts/{identifier}` - Get account details by ID or name
- `GET /api/accounts/{identifier}/validate` - Validate account credentials
- `GET /api/accounts/{identifier}/campaign-types` - Get available campaign types

### System

- `GET /health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Configuration Examples

### Account Configuration (Secret Manager)

Each account has a JSON configuration stored in Secret Manager:

```json
{
  "account_id": "act_123456789",
  "account_name": "nike",
  "display_name": "Nike - US Market",
  "meta": {
    "business_id": "123456789",
    "page_id": "987654321"
  },
  "naming_rules": {
    "traffic_campaign": {
      "campaign": "{client}_{product}_Traffic_{date}",
      "adset": "{client}_{product}_{audience_type}_{date}",
      "ad": "{client}_{product}_{creative_type}_{variant}"
    },
    "conversions_campaign": {
      "campaign": "{client}_{product}_Conv_{objective}_{date}",
      "adset": "{client}_{product}_{funnel_stage}_{date}",
      "ad": "{client}_{product}_{creative_format}_{test_variant}"
    }
  },
  "defaults": {
    "client": "Nike",
    "geo_locations": ["US"],
    "currency": "USD"
  }
}
```

## Documentation

### Setup Guides
- **[Google Secret Manager Setup](docs/google-secret-manager-setup.md)** - Complete Secret Manager configuration
- **[Facebook API Setup](docs/facebook-api-setup.md)** - Getting Meta Marketing API access

### Project Management
- **[Active Tasks](docs/active.md)** - Current tasks and due dates
- **[Decisions Log](docs/decisions.md)** - Architecture decisions

### Naming Conventions

Supports flexible naming with template variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{client}` | Client name | Nike |
| `{product}` | Product name | AirMax |
| `{audience_type}` | Audience targeting | Broad, Lookalike |
| `{date}` | Current date | 2026-02-10 |
| `{creative_type}` | Asset format | image, video |
| `{variant}` | A/B test variant | A, B |

Custom functions supported for complex naming logic.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Development Workflow

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Create pull request
5. Review and merge

## Deployment

### Google Cloud Run (Recommended)

```bash
# Build container
docker build -t gcr.io/PROJECT_ID/exactius-api .

# Push to Container Registry
docker push gcr.io/PROJECT_ID/exactius-api

# Deploy to Cloud Run
gcloud run deploy exactius-api \
  --image gcr.io/PROJECT_ID/exactius-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=PROJECT_ID
```

## Safety & Best Practices

⚠️ **Important**: This platform manages real advertising spend. Always:

- ✅ Test with small budgets first ($5-10)
- ✅ All campaigns start PAUSED for manual review
- ✅ Use Google Secret Manager for credentials (never commit secrets)
- ✅ Implement spending limits at the account level
- ✅ Monitor campaigns regularly
- ✅ Use system user tokens for production (not personal tokens)
- ✅ Audit all changes with logging

## Roadmap

### Phase 1: Backend Foundation ✅ COMPLETE
- [x] Google Secret Manager integration
- [x] Multi-account management
- [x] Account API endpoints
- [x] Configuration system

### Phase 2: Core Workflow (In Progress)
- [ ] Google Drive integration
- [ ] Drive URL parsing and asset download
- [ ] Meta API creative upload
- [ ] Campaign/AdSet/Ad creation
- [ ] Naming resolver with template system
- [ ] Error handling and rollback

### Phase 3: Advanced Features
- [ ] Video asset support
- [ ] Batch operations
- [ ] Campaign preview mode
- [ ] Audit trail logging

### Phase 4: Frontend
- [ ] Next.js frontend application
- [ ] Campaign builder wizard
- [ ] Asset preview and selection
- [ ] Real-time progress tracking
- [ ] Campaign history dashboard

## Troubleshooting

### "Secret not found" error
- Verify secret names follow the format: `exactius-accounts-{ACCOUNT_ID}-{TYPE}`
- Check account ID includes `act_` prefix
- Run `gcloud secrets list | grep exactius` to see all secrets

### "Permission denied" error
- Authenticate: `gcloud auth application-default login`
- Verify IAM permissions: `secretmanager.secretAccessor` role required

### "No accounts configured" error
- Follow [Secret Manager setup guide](docs/google-secret-manager-setup.md)
- Create at least one account configuration

### API server won't start
- Check `GOOGLE_CLOUD_PROJECT` is set in `.env`
- Verify dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is not in use: `lsof -ti:8000`

## Support

For issues or questions:
1. Check the [documentation](docs/)
2. Review [Google Secret Manager Setup](docs/google-secret-manager-setup.md)
3. Test setup with `python scripts/test_secret_manager.py`
4. Check API docs at http://localhost:8000/docs

## License

[Add your license here]
