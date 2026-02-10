# Project Registry

> Master reference for ad accounts and related projects managed by this automation
> platform.

## Active Ad Accounts

| Account Name | Ad Account ID | Purpose | Status |
|---|---|---|---|
| (Main account) | act_XXXXXXXXXX | Primary ad account | Setup pending |

## Cloud Infrastructure

| Service | Purpose | Region | Notes |
|---|---|---|---|
| TBD | TBD | TBD | To be determined based on persistence needs |

## Related Projects

_(No child projects yet - this is currently a single-project setup)_

## Onboarding Checklist

To add a new ad account to the automation platform:
1. Get access to the ad account in Facebook Ads Manager
2. Generate access token with ads_management permissions
3. Add account ID to `.env` file
4. Test API connection with `python src/main.py --account act_XXXXX --test`
5. Update the table above with account details
6. Document any account-specific automation rules in `docs/automation-rules.md`
