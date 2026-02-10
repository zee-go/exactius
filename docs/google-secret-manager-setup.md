# Google Secret Manager Setup Guide

This guide walks through setting up Google Secret Manager for multi-account Meta ads automation.

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured
- Meta Business Manager access with ad accounts
- Meta app created at developers.facebook.com

## Table of Contents

1. [Google Cloud Project Setup](#google-cloud-project-setup)
2. [Shared Credentials Setup](#shared-credentials-setup)
3. [Per-Account Configuration](#per-account-configuration)
4. [IAM Permissions](#iam-permissions)
5. [Local Development Authentication](#local-development-authentication)
6. [Verification](#verification)

---

## 1. Google Cloud Project Setup

### Create or Select Project

```bash
# Create new project
gcloud projects create exactius-ads-automation --name="Exactius Ads"

# Set as active project
gcloud config set project exactius-ads-automation

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Enable other required APIs
gcloud services enable drive.googleapis.com
```

### Set Environment Variable

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export GOOGLE_CLOUD_PROJECT=exactius-ads-automation

# Or create .env file
echo "GOOGLE_CLOUD_PROJECT=exactius-ads-automation" > .env
```

---

## 2. Shared Credentials Setup

These secrets are shared across all ad accounts.

### 2.1 Meta App Credentials

Get these from [Facebook Developer Console](https://developers.facebook.com/apps):

```bash
# Meta App ID
echo -n "YOUR_APP_ID" | gcloud secrets create exactius-shared-meta-app-id \
  --data-file=- \
  --replication-policy="automatic"

# Meta App Secret
echo -n "YOUR_APP_SECRET" | gcloud secrets create exactius-shared-meta-app-secret \
  --data-file=- \
  --replication-policy="automatic"
```

### 2.2 Google Drive Service Account

Create a service account for Google Drive API access:

```bash
# Create service account
gcloud iam service-accounts create exactius-drive-sa \
  --display-name="Exactius Drive Service Account" \
  --description="Service account for accessing Google Drive assets"

# Download service account key
gcloud iam service-accounts keys create drive-service-account-key.json \
  --iam-account=exactius-drive-sa@exactius-ads-automation.iam.gserviceaccount.com

# Upload key to Secret Manager
gcloud secrets create exactius-shared-google-drive-service-account \
  --data-file=drive-service-account-key.json \
  --replication-policy="automatic"

# Delete local key file (now stored securely in Secret Manager)
rm drive-service-account-key.json
```

**Important:** Share your Google Drive folders with the service account email:
- Email: `exactius-drive-sa@exactius-ads-automation.iam.gserviceaccount.com`
- Permission: Viewer (read-only access)

---

## 3. Per-Account Configuration

For each client ad account, create two secrets: access token and configuration.

### 3.1 Meta Access Token

Get a long-lived access token from [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/):

1. Select your app
2. Click "Get User Access Token"
3. Select permissions: `ads_management`, `ads_read`
4. Generate token
5. Extend token to long-lived (60 days) using token exchange endpoint

```bash
# Replace act_123456789 with your actual account ID
ACCOUNT_ID="act_123456789"

# Store access token
echo -n "YOUR_LONG_LIVED_TOKEN" | gcloud secrets create \
  exactius-accounts-${ACCOUNT_ID}-meta-access-token \
  --data-file=- \
  --replication-policy="automatic"
```

### 3.2 Account Configuration

Create a JSON configuration file for each account:

```bash
# Create config file (replace with your values)
cat > account-config.json <<'EOF'
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
    },
    "brand_awareness": {
      "campaign": "{client}_{campaign_name}_Awareness_{geo}_{date}",
      "adset": "{client}_{audience_segment}_{date}",
      "ad": "{client}_{creative_concept}_{format}_{variant}"
    }
  },
  "defaults": {
    "client": "Nike",
    "geo_locations": ["US"],
    "currency": "USD",
    "age_min": 18,
    "age_max": 65
  },
  "budget_limits": {
    "daily_max": 10000,
    "lifetime_max": 100000
  }
}
EOF

# Upload to Secret Manager
gcloud secrets create exactius-accounts-${ACCOUNT_ID}-config \
  --data-file=account-config.json \
  --replication-policy="automatic"

# Clean up
rm account-config.json
```

### Naming Rule Template Variables

Available variables in naming templates:

| Variable | Description | Example |
|----------|-------------|---------|
| `{client}` | Client name from defaults | Nike |
| `{product}` | Product name (user input) | AirMax |
| `{audience_type}` | Audience type (user input) | Broad, Lookalike |
| `{objective}` | Campaign objective | Traffic, Conversions |
| `{date}` | Current date | 2026-02-10 |
| `{timestamp}` | Unix timestamp | 1707580800 |
| `{creative_type}` | Creative format | image, video |
| `{variant}` | A/B test variant | A, B, Control |
| `{geo}` | Geographic target | US, UK, INTL |

Custom variables can be added via the `context` field in API requests.

---

## 4. IAM Permissions

### 4.1 Application Service Account

Create a service account for the application:

```bash
# Create service account
gcloud iam service-accounts create exactius-app \
  --display-name="Exactius Application" \
  --description="Service account for Exactius backend application"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding exactius-ads-automation \
  --member="serviceAccount:exactius-app@exactius-ads-automation.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 4.2 User Access (for local development)

Grant your user account access:

```bash
# Get your user email
GCLOUD_USER=$(gcloud config get-value account)

# Grant access to all secrets
gcloud projects add-iam-policy-binding exactius-ads-automation \
  --member="user:${GCLOUD_USER}" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 5. Local Development Authentication

For local development and testing:

```bash
# Authenticate with your user account
gcloud auth application-default login

# This creates credentials at:
# ~/.config/gcloud/application_default_credentials.json

# Verify authentication
gcloud auth application-default print-access-token
```

---

## 6. Verification

### 6.1 Test Secret Access

```bash
# List all secrets
gcloud secrets list

# Test accessing a secret
gcloud secrets versions access latest --secret="exactius-shared-meta-app-id"
```

### 6.2 Test with Python

Create a test script:

```python
# test_secrets.py
import os
from src.secrets.manager import SecretManagerClient

# Set project ID
os.environ['GOOGLE_CLOUD_PROJECT'] = 'exactius-ads-automation'

# Initialize client
client = SecretManagerClient('exactius-ads-automation')

# List accounts
accounts = client.list_accounts()
print(f"Found {len(accounts)} accounts:")
for acc in accounts:
    print(f"  - {acc['name']} ({acc['display_name']})")

# Test fetching credentials for first account
if accounts:
    account_id = accounts[0]['id']
    print(f"\nTesting credentials for {account_id}...")

    token = client.get_account_token(account_id)
    print(f"  ✓ Access token retrieved (length: {len(token)})")

    config = client.get_account_config(account_id)
    print(f"  ✓ Configuration retrieved")
    print(f"    - Display name: {config['display_name']}")
    print(f"    - Campaign types: {list(config['naming_rules'].keys())}")

    shared = client.get_shared_credentials()
    print(f"  ✓ Shared credentials retrieved")
    print(f"    - App ID: {shared['app_id']}")

print("\n✅ All tests passed!")
```

Run the test:

```bash
python test_secrets.py
```

### 6.3 Test API Server

Start the FastAPI server:

```bash
# Install dependencies first
pip install -r requirements.txt

# Start server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Test endpoints:

```bash
# Health check
curl http://localhost:8000/health

# List accounts
curl http://localhost:8000/api/accounts/

# Get account details
curl http://localhost:8000/api/accounts/nike

# Validate account
curl http://localhost:8000/api/accounts/nike/validate
```

Or open the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Troubleshooting

### Error: "Secret not found"

```bash
# Check if secret exists
gcloud secrets list | grep exactius

# Verify secret name format
# Correct: exactius-accounts-act_123456789-meta-access-token
# Wrong: exactius-accounts-123456789-meta-access-token
```

### Error: "Permission denied"

```bash
# Check IAM permissions
gcloud secrets get-iam-policy exactius-shared-meta-app-id

# Grant yourself access
gcloud secrets add-iam-policy-binding exactius-shared-meta-app-id \
  --member="user:your-email@example.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Application Default Credentials not found"

```bash
# Re-authenticate
gcloud auth application-default login

# Or set GOOGLE_APPLICATION_CREDENTIALS environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/path/to/service-account-key.json
```

---

## Security Best Practices

1. **Never commit credentials to git**
   - Service account keys should only be stored in Secret Manager
   - Use `.gitignore` to exclude `.env` files

2. **Use least privilege IAM roles**
   - Application service accounts: `secretmanager.secretAccessor` only
   - Drive service account: Viewer permission on specific folders only

3. **Rotate access tokens regularly**
   - Meta access tokens expire after 60 days
   - Set up a process to rotate tokens before expiration

4. **Audit secret access**
   ```bash
   # View audit logs
   gcloud logging read "resource.type=secret_manager_secret" --limit 50
   ```

5. **Use secret versions for rollback**
   ```bash
   # Create new version (updates secret)
   echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

   # Rollback to previous version
   gcloud secrets versions enable VERSION_NUMBER --secret=SECRET_NAME
   ```

---

## Adding Additional Accounts

To add a new client account:

1. Get Meta access token for the account
2. Create token secret: `exactius-accounts-{ACCOUNT_ID}-meta-access-token`
3. Create config JSON with naming rules
4. Upload config secret: `exactius-accounts-{ACCOUNT_ID}-config`
5. Test: `curl http://localhost:8000/api/accounts/` (new account should appear)

No code changes or server restart required!

---

## Next Steps

- [API Documentation](./api-documentation.md)
- [Campaign Launch Workflow](./campaign-workflow.md)
- [Naming Conventions Guide](./naming-conventions.md)
