"""
Unit tests for domain errors and serialization.
"""

from zoho_connector.errors import (
    AuthenticationError,
    AuthorizationError,
    InternalConnectorError,
    NotFoundError,
    RateLimitError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
    ValidationError,
    ZohoConnectorError,
)


def test_error_hierarchy():
    assert issubclass(AuthenticationError, ZohoConnectorError)
    assert issubclass(AuthorizationError, ZohoConnectorError)
    assert issubclass(NotFoundError, ZohoConnectorError)
    assert issubclass(RateLimitError, ZohoConnectorError)
    assert issubclass(ValidationError, ZohoConnectorError)
    assert issubclass(UpstreamUnavailableError, ZohoConnectorError)
    assert issubclass(UpstreamTimeoutError, ZohoConnectorError)
    assert issubclass(InternalConnectorError, ZohoConnectorError)


def test_not_found_error_payload():
    err = NotFoundError("Item", "item_404")
    payload = err.to_dict()
    assert payload["error"] is True
    assert payload["code"] == "NOT_FOUND"
    assert payload["retryable"] is False
    assert payload["details"]["resource_type"] == "Item"
    assert payload["details"]["resource_id"] == "item_404"


def test_rate_limit_error_payload():
    err = RateLimitError("Slow down", retry_after_seconds=30)
    payload = err.to_dict()
    assert payload["error"] is True
    assert payload["code"] == "RATE_LIMIT_EXCEEDED"
    assert payload["retryable"] is True
    assert payload["details"]["retry_after_seconds"] == 30


def test_validation_error_payload():
    err = ValidationError("per_page exceeds 50", field="per_page")
    payload = err.to_dict()
    assert payload["error"] is True
    assert payload["code"] == "VALIDATION_ERROR"
    assert payload["details"]["field"] == "per_page"
