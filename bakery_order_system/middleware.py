import datetime
import logging

logger = logging.getLogger(__name__)

class LogRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0]  # Бере першу IP-адресу в списку (якщо є проксі)
        else:
            ip = request.META.get('REMOTE_ADDR')

        logger.info(f"Request: {request.method} {request.path} from {ip}")
        response = self.get_response(request)
        logger.info(f"Response: {response.status_code}")
        return response
