"""
Naming resolver with template-based and custom function support.

Applies client-specific naming rules loaded from account configuration.
Supports:
- Template strings with variable substitution
- Custom Python functions for complex logic
- Auto-generated variables (date, timestamp)
"""

import logging
import importlib
from string import Template
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NamingResolver:
    """Resolves names using client-specific rules."""

    def __init__(self, account_config: Dict[str, Any], campaign_type: str):
        """
        Initialize naming resolver.

        Args:
            account_config: Full account config from Secret Manager
            campaign_type: Type of campaign (traffic_campaign, conversions_campaign, etc.)

        Raises:
            ValueError: If campaign type not found in naming rules
        """
        self.account_config = account_config
        self.campaign_type = campaign_type

        # Get naming rules for this campaign type
        naming_rules = account_config.get('naming_rules', {})
        if campaign_type not in naming_rules:
            available = ', '.join(naming_rules.keys())
            raise ValueError(
                f"Campaign type '{campaign_type}' not found in naming rules. "
                f"Available types: {available}"
            )

        self.rules = naming_rules[campaign_type]
        self.defaults = account_config.get('defaults', {})

        logger.info(f"Initialized naming resolver for {campaign_type}")

    def generate_name(self, entity_type: str, context: Dict[str, Any]) -> str:
        """
        Generate name for entity (campaign, adset, or ad).

        Args:
            entity_type: 'campaign', 'adset', or 'ad'
            context: Variables for template (product, audience_type, etc.)

        Returns:
            Generated name string

        Raises:
            ValueError: If entity type not found in rules
        """
        rule = self.rules.get(entity_type)

        if not rule:
            available = ', '.join(self.rules.keys())
            raise ValueError(
                f"No naming rule for '{entity_type}' in {self.campaign_type}. "
                f"Available entities: {available}"
            )

        # Check if it's a custom function reference
        if isinstance(rule, str) and rule.startswith('custom.'):
            return self._call_custom_function(rule, context)

        # Otherwise, it's a template string
        return self._apply_template(rule, context)

    def _apply_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Apply template with context variables.

        Args:
            template: Template string with {variables}
            context: Variables for substitution

        Returns:
            Resolved name string
        """
        # Merge defaults with context (context overrides defaults)
        full_context = {**self.defaults, **context}

        # Add automatic variables
        full_context['date'] = datetime.now().strftime('%Y-%m-%d')
        full_context['timestamp'] = int(datetime.now().timestamp())
        full_context['account_name'] = self.account_config.get('account_name', 'unknown')
        full_context['account_id'] = self.account_config.get('account_id', 'unknown')

        # Apply template (using safe_substitute to avoid KeyError on missing variables)
        try:
            result = Template(template).safe_substitute(full_context)

            # Check for unresolved variables (will have $ prefix)
            if '$' in result:
                logger.warning(
                    f"Template contains unresolved variables: {template}\n"
                    f"Result: {result}\n"
                    f"Available context: {list(full_context.keys())}"
                )

            return result

        except Exception as e:
            logger.error(f"Template substitution failed: {str(e)}")
            raise ValueError(f"Failed to apply naming template: {str(e)}")

    def _call_custom_function(self, function_path: str, context: Dict[str, Any]) -> str:
        """
        Call custom Python function for complex naming logic.

        Args:
            function_path: Function path like "custom.nike_campaign_namer"
            context: Variables passed to function

        Returns:
            Generated name from custom function

        Raises:
            ValueError: If function not found or execution fails
        """
        try:
            # Parse: "custom.nike_campaign_namer" → module=custom, func=nike_campaign_namer
            # Or: "custom.nike.campaign_namer" → module=custom.nike, func=campaign_namer
            parts = function_path.replace('custom.', '').rsplit('.', 1)

            if len(parts) == 1:
                # Simple case: custom.function_name
                module_name = 'custom'
                func_name = parts[0]
            else:
                # Nested case: custom.module.function_name
                module_name = parts[0]
                func_name = parts[1]

            # Import module
            module = importlib.import_module(f'src.naming.custom.{module_name}')

            # Get function
            func = getattr(module, func_name)

            # Call function with context
            result = func(context)

            if not isinstance(result, str):
                raise ValueError(f"Custom function must return string, got {type(result)}")

            return result

        except ImportError:
            raise ValueError(
                f"Custom naming module not found: '{function_path}'\n"
                f"Create the module at src/naming/custom/{module_name}.py"
            )
        except AttributeError:
            raise ValueError(
                f"Custom naming function not found: '{func_name}' in module '{module_name}'"
            )
        except Exception as e:
            logger.error(f"Custom function execution failed: {str(e)}")
            raise ValueError(f"Custom naming function error: {str(e)}")

    def get_required_variables(self, entity_type: str) -> list:
        """
        Extract required variables from template.

        Args:
            entity_type: 'campaign', 'adset', or 'ad'

        Returns:
            List of variable names required by the template
        """
        rule = self.rules.get(entity_type)
        if not rule or not isinstance(rule, str):
            return []

        # If it's a custom function, we can't determine required variables
        if rule.startswith('custom.'):
            return []

        # Extract variables from template string
        # Find all {variable} patterns
        import re
        variables = re.findall(r'\{(\w+)\}', rule)

        # Filter out auto-generated variables
        auto_vars = {'date', 'timestamp', 'account_name', 'account_id'}
        required = [v for v in variables if v not in auto_vars and v not in self.defaults]

        return list(set(required))  # Remove duplicates

    def preview_names(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate preview of all entity names with given context.

        Args:
            context: Variables for template substitution

        Returns:
            Dictionary with entity_type -> generated_name
        """
        preview = {}

        for entity_type in ['campaign', 'adset', 'ad']:
            try:
                name = self.generate_name(entity_type, context)
                preview[entity_type] = name
            except ValueError as e:
                preview[entity_type] = f"Error: {str(e)}"

        return preview

    def validate_context(self, context: Dict[str, Any]) -> tuple[bool, list]:
        """
        Validate that context has all required variables.

        Args:
            context: Variables provided by user

        Returns:
            Tuple of (is_valid, missing_variables)
        """
        missing = []

        for entity_type in ['campaign', 'adset', 'ad']:
            required = self.get_required_variables(entity_type)
            for var in required:
                if var not in context:
                    missing.append(f"{entity_type}.{var}")

        return (len(missing) == 0, missing)
