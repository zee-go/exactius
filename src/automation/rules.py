"""
Automation rules engine
Define and execute campaign optimization rules
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional

from facebook_business.adobjects.adaccount import AdAccount

logger = logging.getLogger(__name__)


class RuleTrigger(Enum):
    """Types of rule triggers."""
    METRIC_THRESHOLD = 'metric_threshold'
    TIME_BASED = 'time_based'
    BUDGET_THRESHOLD = 'budget_threshold'
    PERFORMANCE_COMPARISON = 'performance_comparison'


class RuleAction(Enum):
    """Types of rule actions."""
    PAUSE_CAMPAIGN = 'pause_campaign'
    ACTIVATE_CAMPAIGN = 'activate_campaign'
    ADJUST_BUDGET = 'adjust_budget'
    ADJUST_BID = 'adjust_bid'
    SEND_ALERT = 'send_alert'


@dataclass
class AutomationRule:
    """Defines an automation rule."""
    name: str
    description: str
    trigger_type: RuleTrigger
    trigger_condition: Callable[[Dict], bool]
    action_type: RuleAction
    action_handler: Callable[[str], None]
    enabled: bool = True

    def evaluate(self, data: Dict) -> bool:
        """
        Evaluate if rule condition is met.

        Args:
            data: Campaign data to evaluate

        Returns:
            True if condition is met
        """
        if not self.enabled:
            return False

        try:
            return self.trigger_condition(data)
        except Exception as e:
            logger.error(f"Error evaluating rule '{self.name}': {str(e)}")
            return False

    def execute(self, campaign_id: str) -> None:
        """
        Execute rule action.

        Args:
            campaign_id: Campaign ID to act on
        """
        try:
            logger.info(f"Executing rule '{self.name}' for campaign {campaign_id}")
            self.action_handler(campaign_id)
            logger.info(f"Rule '{self.name}' executed successfully")
        except Exception as e:
            logger.error(f"Error executing rule '{self.name}': {str(e)}")


class RulesEngine:
    """Manages and executes automation rules."""

    def __init__(self, ad_account: AdAccount):
        """
        Initialize rules engine.

        Args:
            ad_account: AdAccount instance
        """
        self.ad_account = ad_account
        self.rules: List[AutomationRule] = []

    def add_rule(self, rule: AutomationRule) -> None:
        """
        Add an automation rule.

        Args:
            rule: AutomationRule to add
        """
        self.rules.append(rule)
        logger.info(f"Added rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove an automation rule by name.

        Args:
            rule_name: Name of rule to remove

        Returns:
            True if removed, False if not found
        """
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        removed = len(self.rules) < initial_count

        if removed:
            logger.info(f"Removed rule: {rule_name}")
        else:
            logger.warning(f"Rule not found: {rule_name}")

        return removed

    def evaluate_campaign(self, campaign_id: str, campaign_data: Dict) -> None:
        """
        Evaluate all rules for a campaign.

        Args:
            campaign_id: Campaign ID
            campaign_data: Campaign metrics and data
        """
        logger.debug(f"Evaluating rules for campaign {campaign_id}")

        for rule in self.rules:
            if rule.evaluate(campaign_data):
                logger.info(f"Rule '{rule.name}' triggered for campaign {campaign_id}")
                rule.execute(campaign_id)

    def run_automation(self) -> None:
        """
        Run automation checks for all campaigns.
        This would be called periodically (e.g., hourly, daily).
        """
        logger.info("Running automation rules...")

        # TODO: Implement full automation logic
        # 1. Fetch all campaigns
        # 2. Get metrics for each campaign
        # 3. Evaluate rules for each campaign
        # 4. Execute actions for triggered rules
        # 5. Log results

        logger.info("Automation run completed")


# Example rule definitions (to be customized)

def create_low_roas_pause_rule(
    min_roas: float,
    campaign_manager
) -> AutomationRule:
    """
    Create a rule that pauses campaigns with low ROAS.

    Args:
        min_roas: Minimum acceptable ROAS
        campaign_manager: CampaignManager instance

    Returns:
        AutomationRule
    """
    def trigger(data: Dict) -> bool:
        roas = data.get('roas', 0)
        spend = data.get('spend', 0)
        # Only trigger if spend is above threshold
        return spend > 100 and roas < min_roas

    def action(campaign_id: str) -> None:
        campaign_manager.pause_campaign(campaign_id)
        logger.warning(f"Paused campaign {campaign_id} due to low ROAS")

    return AutomationRule(
        name='low_roas_pause',
        description=f'Pause campaigns with ROAS below {min_roas}',
        trigger_type=RuleTrigger.METRIC_THRESHOLD,
        trigger_condition=trigger,
        action_type=RuleAction.PAUSE_CAMPAIGN,
        action_handler=action
    )
