import json
import logging


class JsonFormatter(logging.Formatter):
    """One JSON object per line so Filebeat/Elasticsearch can index it without a grok pattern.

    Pass a dict as the log message (`logger.info({...})`) to get structured
    fields; a plain string message still works and lands under "message".
    If the dict has an "event" key, keep it a nested object (event.category/
    action/outcome) - ECS's index template maps top-level `event` as an
    object, so a plain string there is rejected by Elasticsearch on ingest.
    """

    def format(self, record):
        payload = dict(record.msg) if isinstance(record.msg, dict) else {"message": record.getMessage()}
        payload.setdefault("@timestamp", self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"))
        payload.setdefault("level", record.levelname)
        payload.setdefault("service", "backend")
        payload.setdefault("logger", record.name)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)
