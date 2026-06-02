from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_level: str = "INFO") -> None:
    root_logger = logging.getLogger()

    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.setFormatter(JsonFormatter())
        root_logger.setLevel(log_level.upper())
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())
