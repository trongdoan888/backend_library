import logging
import threading

logger = logging.getLogger("app")
_local = threading.local()


def bind_request(request):
    _local.request = request


def _current_user():
    request = getattr(_local, "request", None)
    return getattr(request, "user", None) if request else None


def current_username():
    user = _current_user()
    return getattr(user, "username", None) if getattr(user, "is_authenticated", False) else None


def current_user_id():
    user = _current_user()
    return str(user.pk) if getattr(user, "is_authenticated", False) else None


def log_event(category, action, outcome, **fields):
    """category/action/outcome follow ECS event.* (e.g. "authentication"/"login"/"success").

    Never pass password/token/secret in `fields` - this is the one place
    that decides what becomes a searchable log line, so keep it that way.
    """
    logger.info({
        "event": {"category": category, "action": action, "outcome": outcome},
        "user": current_username(),
        "user_id": current_user_id(),
        **fields,
    })
