"""
Campaign launch API endpoints.

Provides endpoints for launching campaigns from Google Drive assets.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from src.accounts.manager import AccountManager
from src.orchestrator.campaign_launcher import CampaignLauncher
from src.api.dependencies import get_account_manager
from src.api.models.campaigns import CampaignLaunchRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post(
    "/launch",
    summary="Launch campaign from Drive assets",
    description="Create a Meta ad campaign from Google Drive assets with client-specific naming"
)
async def launch_campaign(
    request: CampaignLaunchRequest,
    account_manager: AccountManager = Depends(get_account_manager)
) -> Dict[str, Any]:
    """
    Launch a campaign from Google Drive assets.

    Workflow:
    1. Download assets from Drive
    2. Validate against Meta specs
    3. Upload to Meta Ad Library
    4. Apply naming rules
    5. Create campaign structure (Campaign → AdSet → Ads)

    All campaigns start PAUSED for manual review.

    Args:
        request: Campaign launch request with Drive URL, account, campaign type, etc.
        account_manager: Account manager dependency

    Returns:
        Launch result with campaign IDs and status
    """
    try:
        logger.info(f"Campaign launch request for account: {request.account_id}")

        # Load account credentials
        account_data = account_manager.load_account_credentials(request.account_id)

        # Validate campaign type exists
        config = account_data['config']
        if request.campaign_type not in config.get('naming_rules', {}):
            available_types = list(config.get('naming_rules', {}).keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type '{request.campaign_type}'. "
                       f"Available: {', '.join(available_types)}"
            )

        # Initialize launcher
        launcher = CampaignLauncher(
            account_config=config,
            account_token=account_data['token'],
            shared_credentials=account_data['shared']
        )

        # Get budget from request or use default
        daily_budget = request.context.get('daily_budget', 1000)  # Default $10
        objective = request.context.get('objective', 'LINK_CLICKS')

        # Launch campaign
        result = launcher.launch_campaign(
            drive_url=request.drive_url,
            campaign_type=request.campaign_type,
            context=request.context,
            daily_budget=daily_budget,
            objective=objective,
            preview_only=request.preview_only
        )

        # Return result
        if result.success:
            status_code = status.HTTP_200_OK if request.preview_only else status.HTTP_201_CREATED
            return {
                "status": "success",
                "preview_only": request.preview_only,
                "data": result.to_dict()
            }
        else:
            return {
                "status": "error",
                "errors": result.errors,
                "warnings": result.warnings,
                "data": result.to_dict()
            }

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Campaign launch failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Campaign launch failed: {str(e)}"
        )


@router.post(
    "/preview",
    summary="Preview campaign without creating",
    description="Validate assets and preview naming without actually creating campaigns"
)
async def preview_campaign(
    request: CampaignLaunchRequest,
    account_manager: AccountManager = Depends(get_account_manager)
) -> Dict[str, Any]:
    """
    Preview campaign creation without actually creating.

    Useful for:
    - Validating Drive assets
    - Testing naming rules
    - Checking required variables

    Args:
        request: Campaign launch request
        account_manager: Account manager dependency

    Returns:
        Preview result with asset list and generated names
    """
    # Force preview mode
    request.preview_only = True

    return await launch_campaign(request, account_manager)
