from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import ClassVar


class PiiRedactFilter(logging.Filter):
    """Redacts PII (emails, DNI, CUIL, CBU) from log messages.

    Must be installed on EVERY logger because ``logging.Filter`` does
    **not** follow the logger hierarchy — only handlers do. Use
    :func:`install_pii_filter` to add this filter to all existing
    and future loggers at once.
    """

    _PII_PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        # Email addresses
        (re.compile(r"[\w.+-]+@[\w-]+\.[\w.+-]+"), "[REDACTED]"),
        # Argentine DNI (7–8 digits, whole word)
        (re.compile(r"\b\d{7,8}\b"), "[REDACTED]"),
        # Argentine CUIL/CUIT (11 consecutive digits)
        (re.compile(r"\b\d{11}\b"), "[REDACTED]"),
        # Argentine CBU (22 consecutive digits)
        (re.compile(r"\b\d{22}\b"), "[REDACTED]"),
    ]

    # Cache of logger names we already warned about (avoids log-spam)
    _warned: ClassVar[set[str]] = set()

    def filter(self, record: logging.LogRecord) -> bool:
        """Modify *record.msg* in-place, redacting all PII patterns.

        Always returns ``True`` so the record is never discarded.
        """
        if not isinstance(record.msg, str):
            return True

        original = record.msg
        for pattern, replacement in self._PII_PATTERNS:
            record.msg = pattern.sub(replacement, record.msg)

        # Warn once per logger so devs know they're logging PII
        if record.msg != original and record.name not in self._warned:
            self._warned.add(record.name)
            # Use print() to avoid infinite recursion in logging
            print(
                f"[PII REDACTED] Logger '{record.name}' emitted PII — "
                f"review the source and move PII out of log messages.",
                flush=True,
            )

        return True


# Singleton filter instance (reused to keep _warned set consistent)
_PII_FILTER = PiiRedactFilter()


def install_pii_filter() -> None:
    """Install :class:`PiiRedactFilter` on every logger.

    Python's ``logging.Filter`` does **not** propagate through the
    logger hierarchy, so a filter on the root logger has **no effect**
    on child loggers. This function:

    1. Adds the filter to **every** currently-registered logger.
    2. Monkey-patches ``logging.getLogger`` so newly-created loggers
       get the filter automatically.

    Safe to call multiple times — it checks for duplicates.
    """
    # ── 1. Add to all existing loggers ─────────────────────────────────
    for name in list(logging.Logger.manager.loggerDict):
        logger = logging.getLogger(name)
        if not _has_pii_filter(logger):
            logger.addFilter(_PII_FILTER)

    # ── 2. Patch getLogger for new loggers ────────────────────────────
    _original_get_logger = logging.getLogger

    def _pii_get_logger(name: str | None = None) -> logging.Logger:
        logger = _original_get_logger(name)
        if not _has_pii_filter(logger):
            logger.addFilter(_PII_FILTER)
        return logger

    logging.getLogger = _pii_get_logger


def _has_pii_filter(logger: logging.Logger) -> bool:
    return any(isinstance(f, PiiRedactFilter) for f in logger.filters)


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
    # Ensure PII redaction is installed on ALL loggers
    install_pii_filter()

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
