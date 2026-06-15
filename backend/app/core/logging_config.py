"""
Structured JSON logging for CloudWatch Logs Insights queries.

In production, logs are output as single-line JSON for easy parsing.
In development, logs use a human-readable format.
"""
import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Output log records as single-line JSON for CloudWatch parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(environment: str = "development"):
    """
    Configure root logger based on environment.

    Args:
        environment: "production" for JSON output, anything else for readable format.
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )
        )

    root.handlers.clear()
    root.addHandler(handler)
