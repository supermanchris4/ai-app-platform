"""JSON logging (specs/20-api-scaffold.md#logging). Platform module: imports nothing from the domain.

Every log line is one JSON object on standard output, with the timestamp (UTC, ISO 8601), level,
logger, message, correlation ID and request ID, plus every field passed through `extra` except those
in the deny list. Exceptions are logged by type and stack frames, without their messages.
"""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Set by the correlation middleware for the request being handled; None outside a request.
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# `extra` fields that are never logged, compared without regard to case.
DENIED_FIELDS = frozenset({"authorization", "cookie", "token", "password", "email", "name", "oid", "subject"})

# Attributes every LogRecord has; anything else on a record came from `extra`. uvicorn's
# `color_message` repeats the message with terminal colour codes.
_RECORD_ATTRIBUTES = frozenset(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {
    "message",
    "asctime",
    "color_message",
}


class JsonFormatter(logging.Formatter):
    """Formats each record as one JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(),
            "request_id": request_id_var.get(),
        }
        for key, value in vars(record).items():
            if key not in _RECORD_ATTRIBUTES and key.lower() not in DENIED_FIELDS:
                entry[key] = value
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = describe_exception(record.exc_info[1])
        return json.dumps(entry, default=str)


def describe_exception(exc: BaseException) -> list[dict[str, str]]:
    """Each exception in the chain by type and stack frames, without its message.

    Messages are left out because they can hold personal information: a database error, for example,
    repeats the values of the row it refused. The frames show the code, never the values.
    """
    chain: list[dict[str, str]] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(
            {
                "type": f"{type(current).__module__}.{type(current).__qualname__}",
                "traceback": "".join(traceback.format_tb(current.__traceback__)),
            }
        )
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return chain


def configure_logging(level: str) -> None:
    """Send every logger, uvicorn's included, through the JSON formatter on standard output.

    uvicorn's access log is turned off: it logs full paths, which can hold identifiers. The request
    logging middleware logs each request with its path template instead. HTTP client libraries log
    only warnings and errors.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
    # HTTP clients log every URL they call, which can hold identifiers or codes.
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
