"""
Account management API endpoints.

Provides endpoints for:
- Listing available ad accounts
- Getting account details
- Validating account access
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from src.accounts.manager import AccountManager
from src.api.dependencies import get_account_manager
from src.api.models.accounts import (
    AccountInfo,
    AccountListResponse,
    AccountDetail
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get(
    "/",
    response_model=AccountListResponse,
    summary="List all accounts",
    description="Get a list of all configured ad accounts from Secret Manager"
)
async def list_accounts(
    account_manager: AccountManager = Depends(get_account_manager)
) -> AccountListResponse:
    """
    List all available ad accounts.

    Returns:
        AccountListResponse with list of accounts and count
    """
    try:
        logger.info("Fetching account list")
        accounts = account_manager.list_accounts()

        # Convert to Pydantic models
        account_infos = [
            AccountInfo(
                id=acc['id'],
                name=acc['name'],
                display_name=acc['display_name']
            )
            for acc in accounts
        ]

        return AccountListResponse(
            accounts=account_infos,
            count=len(account_infos)
        )

    except ValueError as e:
        logger.error(f"Error listing accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error listing accounts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list accounts"
        )


@router.get(
    "/{account_identifier}",
    response_model=AccountDetail,
    summary="Get account details",
    description="Get detailed information about a specific account by ID or name"
)
async def get_account(
    account_identifier: str,
    account_manager: AccountManager = Depends(get_account_manager)
) -> AccountDetail:
    """
    Get detailed account information.

    Args:
        account_identifier: Account ID (act_123456789) or name (nike)

    Returns:
        AccountDetail with full account configuration
    """
    try:
        logger.info(f"Fetching details for account: {account_identifier}")
        account_data = account_manager.get_account(account_identifier)

        config = account_data['config']

        return AccountDetail(
            account_id=config['account_id'],
            account_name=config['account_name'],
            display_name=config['display_name'],
            campaign_types=list(config['naming_rules'].keys()),
            naming_rules=config['naming_rules'],
            defaults=config.get('defaults', {}),
            meta=config.get('meta')
        )

    except ValueError as e:
        logger.error(f"Account not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account details"
        )


@router.get(
    "/{account_identifier}/validate",
    summary="Validate account access",
    description="Check if account credentials and configuration are valid"
)
async def validate_account(
    account_identifier: str,
    account_manager: AccountManager = Depends(get_account_manager)
) -> dict:
    """
    Validate account access and configuration.

    Args:
        account_identifier: Account ID (act_123456789) or name (nike)

    Returns:
        Validation result with status and any issues
    """
    try:
        logger.info(f"Validating account: {account_identifier}")

        # First get the account to verify it exists
        account_data = account_manager.get_account(account_identifier)
        account_id = account_data['account_id']

        # Validate access
        is_valid = account_manager.validate_account_access(account_id)

        if is_valid:
            return {
                "status": "valid",
                "account_id": account_id,
                "message": "Account credentials and configuration are valid"
            }
        else:
            return {
                "status": "invalid",
                "account_id": account_id,
                "message": "Account validation failed. Check logs for details."
            }

    except ValueError as e:
        logger.error(f"Account not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error validating account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate account"
        )


@router.get(
    "/{account_identifier}/campaign-types",
    summary="Get available campaign types",
    description="Get list of campaign types available for this account"
)
async def get_campaign_types(
    account_identifier: str,
    account_manager: AccountManager = Depends(get_account_manager)
) -> dict:
    """
    Get available campaign types for an account.

    Args:
        account_identifier: Account ID (act_123456789) or name (nike)

    Returns:
        List of campaign type names
    """
    try:
        logger.info(f"Fetching campaign types for account: {account_identifier}")

        # Get account to verify it exists
        account_data = account_manager.get_account(account_identifier)
        account_id = account_data['account_id']

        # Get campaign types
        campaign_types = account_manager.get_campaign_types(account_id)

        return {
            "account_id": account_id,
            "campaign_types": campaign_types,
            "count": len(campaign_types)
        }

    except ValueError as e:
        logger.error(f"Account not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching campaign types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch campaign types"
        )
