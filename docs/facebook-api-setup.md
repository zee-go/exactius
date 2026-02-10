# Facebook Marketing API Setup Guide

Complete guide to setting up Facebook Marketing API access for campaign automation.

## Prerequisites

1. Facebook account with access to a Facebook Business Manager
2. Admin or Developer access to the ad account you want to manage
3. Python 3.12+ installed locally

## Step 1: Create a Facebook App

1. Go to https://developers.facebook.com/apps
2. Click "Create App"
3. Choose app type: "Business" (recommended for ads automation)
4. Fill in app details:
   - App name: "Exactius Ads Automation" (or your preferred name)
   - App contact email: your email
   - Business account: select your business (or create one)
5. Click "Create App"
6. Note your App ID and App Secret (go to Settings > Basic)

## Step 2: Get Marketing API Access

1. In your app dashboard, go to "Add Products"
2. Find "Marketing API" and click "Set Up"
3. Complete the following:
   - Standard Access requires business verification (takes 3-7 days)
   - During verification, you can use Development Mode for testing
4. Add your ad account: Marketing API > Tools > Ad Accounts
5. Request appropriate permissions:
   - `ads_management` (required for campaign automation)
   - `ads_read` (required for reading campaign data)
   - `business_management` (optional, for managing business assets)

## Step 3: Generate Access Token

### Option A: Short-lived Token (for testing)

1. Go to Graph API Explorer: https://developers.facebook.com/tools/explorer
2. Select your app from the dropdown
3. Add permissions: `ads_management`, `ads_read`
4. Click "Generate Access Token"
5. Copy the token (valid for ~1 hour)

### Option B: Long-lived Token (for production)

```bash
# Exchange short-lived token for long-lived token (60 days)
curl -X GET "https://graph.facebook.com/v19.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_LIVED_TOKEN"
```

### Option C: System User Token (recommended for automation)

1. Go to Business Settings > Users > System Users
2. Create a new system user or select existing
3. Add assets: assign your ad account to the system user
4. Generate token: click "Generate New Token"
5. Select permissions: `ads_management`, `ads_read`
6. Copy the token (never expires unless manually revoked)

## Step 4: Find Your Ad Account ID

1. Go to Facebook Ads Manager: https://business.facebook.com/adsmanager
2. Look in the URL for your account ID
3. Format: URL will show `act=123456789` → your account ID is `act_123456789`
4. Or: Go to Ad Account Settings → Account Info → Ad Account ID

## Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Facebook API Credentials
FB_ACCESS_TOKEN=your_access_token_here
FB_APP_ID=your_app_id_here
FB_APP_SECRET=your_app_secret_here
FB_AD_ACCOUNT_ID=act_123456789

# Optional Configuration
FB_API_VERSION=v19.0
LOG_LEVEL=INFO
```

## Step 6: Test API Connection

```bash
# Install dependencies
pip install -r requirements.txt

# Test connection (once implemented)
python src/main.py --test-connection
```

## Security Best Practices

1. **Never commit credentials**: Ensure `.env` is in `.gitignore`
2. **Use system user tokens**: More secure than personal access tokens
3. **Rotate tokens regularly**: Even long-lived tokens should be rotated
4. **Limit permissions**: Only request permissions you actually need
5. **Monitor usage**: Check for suspicious API activity in Facebook Events Manager
6. **Use environment-specific tokens**: Different tokens for dev/staging/prod

## Troubleshooting

### "Invalid OAuth 2.0 Access Token"
- Token expired (generate new one)
- Token doesn't have required permissions
- App is in Development Mode but token is from different user

### "Application does not have permission for this action"
- Your app needs Marketing API access (may require business verification)
- Ad account not assigned to your app or system user
- Missing required permissions in token

### "User does not have permission to access this ad account"
- Your Facebook account lacks admin/advertiser access to the ad account
- Ad account not added to your Business Manager
- System user not assigned to the ad account

## Rate Limits

Facebook Marketing API has the following limits:
- **Standard Access**: 200 calls per hour per user
- **Graph API**: 200 calls per hour per app per user
- **Batch requests**: Can combine up to 50 calls in one request
- **Ad creation**: Rate limited separately (varies by account)

Implement exponential backoff and respect rate limit headers:
- `x-business-use-case-usage`
- `x-app-usage`

## Useful Resources

- Facebook Marketing API Docs: https://developers.facebook.com/docs/marketing-apis
- API Reference: https://developers.facebook.com/docs/marketing-api/reference
- Graph API Explorer: https://developers.facebook.com/tools/explorer
- Business Manager: https://business.facebook.com
- Facebook for Developers Support: https://developers.facebook.com/support
