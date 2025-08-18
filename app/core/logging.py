import logging
import sys
import json
from typing import Any, MutableMapping

from app.core.config import settings

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: MutableMapping[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        # Attach request id if present
        request_id = getattr(record, "request_id", None)
        if request_id:
            base["request_id"] = request_id
        return json.dumps(base, ensure_ascii=False)

def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root.handlers = [handler]
