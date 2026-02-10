#!/usr/bin/env python3
"""
Test script for Google Secret Manager integration.

Verifies that:
1. Secret Manager client can connect
2. Accounts are configured correctly
3. Credentials can be retrieved
4. Configuration is valid
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from secrets.manager import SecretManagerClient
from accounts.manager import AccountManager


def main():
    """Run Secret Manager integration tests."""
    print("=" * 70)
    print("Exactius - Secret Manager Integration Test")
    print("=" * 70)
    print()

    # Load environment
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✓ Loaded .env file")
    else:
        print("⚠ No .env file found (using environment variables)")

    # Check for project ID
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("✗ GOOGLE_CLOUD_PROJECT environment variable not set")
        print("\nPlease set GOOGLE_CLOUD_PROJECT in your .env file or environment:")
        print("  export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)

    print(f"✓ Google Cloud Project: {project_id}")
    print()

    # Initialize Secret Manager client
    print("=" * 70)
    print("1. Testing Secret Manager Connection")
    print("=" * 70)

    try:
        secret_manager = SecretManagerClient(project_id)
        print("✓ Secret Manager client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Secret Manager client: {str(e)}")
        sys.exit(1)

    print()

    # Test listing accounts
    print("=" * 70)
    print("2. Listing Configured Accounts")
    print("=" * 70)

    try:
        accounts = secret_manager.list_accounts()
        print(f"✓ Found {len(accounts)} configured account(s):")
        print()

        for i, acc in enumerate(accounts, 1):
            print(f"  {i}. {acc['name']} - {acc['display_name']}")
            print(f"     ID: {acc['id']}")
            print()

        if not accounts:
            print("⚠ No accounts configured yet")
            print("\nTo add an account, see docs/google-secret-manager-setup.md")
            sys.exit(0)

    except Exception as e:
        print(f"✗ Failed to list accounts: {str(e)}")
        sys.exit(1)

    # Test fetching shared credentials
    print("=" * 70)
    print("3. Testing Shared Credentials")
    print("=" * 70)

    try:
        shared = secret_manager.get_shared_credentials()
        print("✓ Shared credentials retrieved:")
        print(f"  - App ID: {shared['app_id']}")
        print(f"  - App Secret: {'*' * 20}... (length: {len(shared['app_secret'])})")
        print(f"  - Drive SA: {'*' * 20}... (length: {len(shared['drive_service_account'])})")
    except Exception as e:
        print(f"✗ Failed to retrieve shared credentials: {str(e)}")
        print("\nMake sure you've created the shared secrets:")
        print("  - exactius-shared-meta-app-id")
        print("  - exactius-shared-meta-app-secret")
        print("  - exactius-shared-google-drive-service-account")
        sys.exit(1)

    print()

    # Test each account
    print("=" * 70)
    print("4. Testing Account Credentials")
    print("=" * 70)

    account_manager = AccountManager(secret_manager)
    all_valid = True

    for acc in accounts:
        account_id = acc['id']
        account_name = acc['name']

        print(f"\nTesting: {account_name} ({account_id})")
        print("-" * 70)

        # Test access token
        try:
            token = secret_manager.get_account_token(account_id)
            print(f"  ✓ Access token retrieved (length: {len(token)})")
        except Exception as e:
            print(f"  ✗ Failed to retrieve access token: {str(e)}")
            all_valid = False
            continue

        # Test configuration
        try:
            config = secret_manager.get_account_config(account_id)
            print(f"  ✓ Configuration retrieved")
            print(f"    - Display name: {config['display_name']}")
            print(f"    - Campaign types: {', '.join(config['naming_rules'].keys())}")

            if 'defaults' in config:
                print(f"    - Defaults: {len(config['defaults'])} values")
            if 'meta' in config:
                print(f"    - Meta business ID: {config['meta'].get('business_id', 'N/A')}")

        except Exception as e:
            print(f"  ✗ Failed to retrieve configuration: {str(e)}")
            all_valid = False
            continue

        # Validate account
        is_valid = account_manager.validate_account_access(account_id)
        if is_valid:
            print(f"  ✓ Account validation passed")
        else:
            print(f"  ✗ Account validation failed")
            all_valid = False

    print()
    print("=" * 70)
    print("5. Summary")
    print("=" * 70)

    if all_valid:
        print("✅ All tests passed!")
        print("\nYou can now:")
        print("  1. Start the API server: python -m uvicorn src.api.main:app --reload")
        print("  2. View API docs: http://localhost:8000/docs")
        print("  3. Test endpoints: curl http://localhost:8000/api/accounts/")
    else:
        print("⚠ Some tests failed. Please review the errors above.")
        print("\nRefer to docs/google-secret-manager-setup.md for setup instructions.")
        sys.exit(1)


if __name__ == '__main__':
    main()
