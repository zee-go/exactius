"""
Retry and rate-limit handling for Facebook Marketing API calls.

Facebook API error codes:
- 4:   Application request limit reached (rate limit)
- 17:  User request limit reached (rate limit)
- 32:  Page-level throttling
- 613: Custom audience throttling
- 1:   Unknown error (transient)
- 2:   Service temporarily unavailable (transient)
- 341: Marketing API limit reached
"""

import time
import logging
import functools
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

# Facebook API error codes that indicate rate limiting
RATE_LIMIT_CODES = {4, 17, 32, 341, 613}

# Facebook API error codes that indicate transient failures worth retrying
TRANSIENT_ERROR_CODES = {1, 2}

# Default retry settings
DEFAULT_MAX_RETRIES = 4
DEFAULT_BASE_DELAY = 2.0   # seconds
DEFAULT_MAX_DELAY = 60.0   # seconds

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
) -> Callable[[F], F]:
    """
    Decorator that retries a function on Facebook API rate limits and transient errors.

    Uses exponential backoff: delay doubles each attempt, capped at max_delay.

    Args:
        max_retries: Maximum number of retry attempts (default 4)
        base_delay: Initial delay in seconds (default 2.0)
        max_delay: Maximum delay in seconds (default 60.0)

    Usage:
        @with_retry(max_retries=3)
        def upload_image(self, path):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as exc:
                    last_exception = exc
                    error_code = _extract_fb_error_code(exc)
                    is_retriable = error_code in RATE_LIMIT_CODES or error_code in TRANSIENT_ERROR_CODES

                    if not is_retriable or attempt == max_retries:
                        raise

                    delay = min(base_delay * (2 ** attempt), max_delay)

                    if error_code in RATE_LIMIT_CODES:
                        logger.warning(
                            f"Facebook API rate limit hit (code {error_code}) in "
                            f"{func.__name__}. Retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                    else:
                        logger.warning(
                            f"Transient Facebook API error (code {error_code}) in "
                            f"{func.__name__}. Retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )

                    time.sleep(delay)

            raise last_exception  # unreachable, but satisfies type checkers

        return wrapper  # type: ignore[return-value]
    return decorator


def _extract_fb_error_code(exc: Exception) -> int | None:
    """
    Extract Facebook API error code from an exception.

    facebook-business SDK raises FacebookRequestError which has api_error_code().
    Returns None for non-Facebook exceptions.
    """
    # facebook-business SDK error
    if hasattr(exc, 'api_error_code'):
        try:
            return int(exc.api_error_code())
        except (TypeError, ValueError):
            pass

    # Sometimes wrapped in a ValueError with the FB error inside
    cause = getattr(exc, '__cause__', None) or getattr(exc, '__context__', None)
    if cause and hasattr(cause, 'api_error_code'):
        try:
            return int(cause.api_error_code())
        except (TypeError, ValueError):
            pass

    return None
