import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings with request ID and timestamps,
    stripping sensitive data like passwords or tokens.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "client_ip"):
            log_obj["client_ip"] = getattr(record, "client_ip")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Sanitize sensitive fields if extra dict was passed
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            sanitized = {}
            for k, v in record.extra_data.items():
                if k.lower() in ("password", "token", "authorization", "cookie", "secret", "access_token"):
                    sanitized[k] = "[REDACTED]"
                else:
                    sanitized[k] = v
            log_obj["extra"] = sanitized

        return json.dumps(log_obj)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("pagemetrics")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger


logger = setup_logging()
