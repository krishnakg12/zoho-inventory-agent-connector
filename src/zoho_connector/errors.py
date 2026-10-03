"""
Domain error classes for Zoho Inventory MCP Connector.
Translates all upstream HTTP and connector errors into safe, structured domain errors.
Ensures zero credential leakage to AI agents.
"""

from typing import Any, Dict, Optional


class ZohoConnectorError(Exception):
    """Base exception for all Zoho Connector errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to a safe, agent-facing dictionary."""
        payload: Dict[str, Any] = {
            "error": True,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class AuthenticationError(ZohoConnectorError):
    """Raised when OAuth authentication or token refresh fails."""

    def __init__(
        self,
        message: str = "Authentication with Zoho failed. Please check credentials.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            retryable=False,
            details=details,
        )


class AuthorizationError(ZohoConnectorError):
    """Raised when access is forbidden or permissions/scopes are insufficient."""

    def __init__(
        self,
        message: str = "Access forbidden. Ensure the OAuth token has the required read scope.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            retryable=False,
            details=details,
        )


class NotFoundError(ZohoConnectorError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
    ):
        msg = message or f"{resource_type} with ID '{resource_id}' was not found in Zoho Inventory."
        super().__init__(
            message=msg,
            code="NOT_FOUND",
            retryable=False,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class RateLimitError(ZohoConnectorError):
    """Raised when Zoho or local client rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please back off before retrying.",
        retry_after_seconds: Optional[int] = None,
    ):
        details = {}
        if retry_after_seconds is not None:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            retryable=True,
            details=details,
        )
        self.retry_after_seconds = retry_after_seconds


class ValidationError(ZohoConnectorError):
    """Raised when input parameters fail validation constraints."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        d = details or {}
        if field:
            d["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            retryable=False,
            details=d,
        )


class UpstreamUnavailableError(ZohoConnectorError):
    """Raised when Zoho Inventory API is temporarily unavailable (500/502/503/504)."""

    def __init__(
        self,
        message: str = "Zoho Inventory service is temporarily unavailable. Please retry later.",
        status_code: Optional[int] = None,
    ):
        details = {}
        if status_code:
            details["upstream_status"] = status_code
        super().__init__(
            message=message,
            code="UPSTREAM_UNAVAILABLE",
            retryable=True,
            details=details,
        )


class UpstreamTimeoutError(ZohoConnectorError):
    """Raised when a request to Zoho Inventory API times out."""

    def __init__(
        self,
        message: str = "Request to Zoho Inventory API timed out.",
        timeout_seconds: Optional[float] = None,
    ):
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            code="UPSTREAM_TIMEOUT",
            retryable=True,
            details=details,
        )


class InternalConnectorError(ZohoConnectorError):
    """Raised for unexpected internal errors in the connector."""

    def __init__(
        self,
        message: str = "An internal error occurred in the Zoho connector.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="INTERNAL_CONNECTOR_ERROR",
            retryable=False,
            details=details,
        )
