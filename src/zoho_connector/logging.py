"""
Structured logging and security redaction for Zoho Inventory MCP Connector.
Ensures zero sensitive credential leakage in all standard and structured logs.
"""

import json
import logging
import re
import sys
from typing import Any, Dict

# Regex patterns for sensitive credentials that must never appear in logs
SENSITIVE_PATTERNS = [
    (re.compile(r"Zoho-oauthtoken\s+[^\s,'\"]+", re.IGNORECASE), "Zoho-oauthtoken [REDACTED]"),
    (re.compile(r"Bearer\s+[^\s,'\"]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"(client_secret[=:]\s*)[^\s,'\"&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(refresh_token[=:]\s*)[^\s,'\"&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(access_token[=:]\s*)[^\s,'\"&]+", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(client_id[=:]\s*)[^\s,'\"&]+", re.IGNORECASE), r"\1[REDACTED]"),
]


def redact_sensitive_data(text: str) -> str:
    """Redact tokens, credentials, and sensitive headers from a string."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts secrets from all log record messages and arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg and isinstance(record.msg, str):
            record.msg = redact_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_sensitive_data(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_sensitive_data(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True


class JsonFormatter(logging.Formatter):
    """Formats log records as structured JSON with standardized observability fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_data(record.getMessage()),
        }

        # Include structured context fields if present
        for field in [
            "request_id",
            "tool_name",
            "operation",
            "latency_ms",
            "upstream_status",
            "retry_count",
            "result_count",
            "error_code",
        ]:
            if hasattr(record, field):
                val = getattr(record, field)
                if isinstance(val, str):
                    val = redact_sensitive_data(val)
                log_payload[field] = val

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """Configure connector root logger with security filters and proper formatting."""
    logger = logging.getLogger("zoho_connector")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    # Remove existing handlers to avoid duplicates
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    # Use stderr so stdout remains purely reserved for MCP stdio JSON-RPC
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(SensitiveDataFilter())

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the zoho_connector namespace."""
    return logging.getLogger(f"zoho_connector.{name}")
