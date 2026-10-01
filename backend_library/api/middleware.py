import time

from api.audit import bind_request, current_user_id, current_username, logger


class AccessLogMiddleware:
    """Giai đoạn 2.B - Access Logging: 1 dòng log cho MỌI request/response.

    Đặt sau AuthenticationMiddleware trong MIDDLEWARE nên request.user đã có
    khi response quay lại đây (DRF's Request.user setter ghi ngược vào
    request gốc, nên vẫn đúng cả với JWTAuthentication của DRF).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        bind_request(request)
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info({
            "event": {
                "category": "web",
                "action": "http_request",
                "outcome": "success" if response.status_code < 400 else "failure",
            },
            "method": request.method,
            "endpoint": request.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "user": current_username(),
            "user_id": current_user_id(),
            "ip": request.META.get("REMOTE_ADDR"),
        })
        return response
