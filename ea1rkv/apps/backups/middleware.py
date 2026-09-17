from django.conf import settings
from django.http import HttpResponse


class RestoreMaintenanceMiddleware:
    """Return a clear 503 while a database/files restore is in progress."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        marker = settings.BACKUP_ROOT / ".restore-in-progress"
        if marker.exists():
            response = HttpResponse(
                "EA1RKV está restaurando una copia de seguridad. "
                "Vuelve a intentarlo en unos minutos.",
                status=503,
                content_type="text/plain; charset=utf-8",
            )
            response["Retry-After"] = "60"
            return response
        return self.get_response(request)
