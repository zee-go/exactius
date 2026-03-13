"""
Tests for the @with_retry decorator.

Mocks time.sleep to avoid real waits.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from src.utils.retry import with_retry, _extract_fb_error_code


def make_fb_error(code):
    """Create a mock FacebookRequestError with a given error code."""
    exc = Exception(f"Facebook API error {code}")
    exc.api_error_code = lambda: code
    return exc


class TestExtractFbErrorCode:

    def test_extracts_from_api_error_code_method(self):
        exc = make_fb_error(17)
        assert _extract_fb_error_code(exc) == 17

    def test_returns_none_for_plain_exception(self):
        exc = ValueError("plain error")
        assert _extract_fb_error_code(exc) is None

    def test_extracts_from_chained_cause(self):
        inner = make_fb_error(4)
        outer = Exception("wrapped")
        outer.__cause__ = inner
        assert _extract_fb_error_code(outer) == 4


class TestWithRetryDecorator:

    def test_success_on_first_try(self):
        mock_fn = MagicMock(return_value="ok")

        @with_retry(max_retries=3)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep") as mock_sleep:
            result = fn()

        assert result == "ok"
        assert mock_fn.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.parametrize("error_code", [4, 17, 32, 341, 613])
    def test_retries_on_rate_limit_codes(self, error_code):
        fb_error = make_fb_error(error_code)
        mock_fn = MagicMock(side_effect=[fb_error, fb_error, "ok"])

        @with_retry(max_retries=3, base_delay=1.0)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep"):
            result = fn()

        assert result == "ok"
        assert mock_fn.call_count == 3

    @pytest.mark.parametrize("error_code", [1, 2])
    def test_retries_on_transient_codes(self, error_code):
        fb_error = make_fb_error(error_code)
        mock_fn = MagicMock(side_effect=[fb_error, "ok"])

        @with_retry(max_retries=3, base_delay=1.0)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep"):
            result = fn()

        assert result == "ok"
        assert mock_fn.call_count == 2

    def test_does_not_retry_non_retriable_error(self):
        fb_error = make_fb_error(100)  # Not in rate limit or transient codes
        mock_fn = MagicMock(side_effect=fb_error)

        @with_retry(max_retries=3)
        def fn():
            return mock_fn()

        with pytest.raises(Exception):
            fn()

        assert mock_fn.call_count == 1  # No retries

    def test_does_not_retry_plain_exception(self):
        mock_fn = MagicMock(side_effect=ValueError("bad input"))

        @with_retry(max_retries=3)
        def fn():
            return mock_fn()

        with pytest.raises(ValueError):
            fn()

        assert mock_fn.call_count == 1

    def test_raises_after_max_retries_exhausted(self):
        fb_error = make_fb_error(17)
        mock_fn = MagicMock(side_effect=fb_error)

        @with_retry(max_retries=2, base_delay=1.0)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep"):
            with pytest.raises(Exception):
                fn()

        # Called max_retries + 1 times (initial + retries)
        assert mock_fn.call_count == 3

    def test_exponential_backoff_sleep_delays(self):
        fb_error = make_fb_error(17)
        # Fail twice, succeed on third
        mock_fn = MagicMock(side_effect=[fb_error, fb_error, "ok"])

        @with_retry(max_retries=3, base_delay=2.0, max_delay=60.0)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep") as mock_sleep:
            fn()

        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_calls[0] == 2.0   # base_delay * 2^0
        assert sleep_calls[1] == 4.0   # base_delay * 2^1

    def test_max_delay_capped(self):
        fb_error = make_fb_error(17)
        attempts = [fb_error] * 4 + ["ok"]
        mock_fn = MagicMock(side_effect=attempts)

        @with_retry(max_retries=5, base_delay=2.0, max_delay=5.0)
        def fn():
            return mock_fn()

        with patch("src.utils.retry.time.sleep") as mock_sleep:
            fn()

        for c in mock_sleep.call_args_list:
            assert c.args[0] <= 5.0

    def test_preserves_function_return_value(self):
        @with_retry(max_retries=1)
        def fn():
            return {"key": "value", "num": 42}

        result = fn()
        assert result == {"key": "value", "num": 42}

    def test_preserves_function_name(self):
        @with_retry()
        def my_function():
            pass

        assert my_function.__name__ == "my_function"
