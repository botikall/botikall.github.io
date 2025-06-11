from .models import ActionLog
from .anomaly_detector import detect_last_log_anomaly

def log_action(request, action, model_name, object_id=None, description=''):
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

    ActionLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    detect_last_log_anomaly()

def get_client_ip(request):
    """Надійне отримання IP-адреси з урахуванням reverse proxy."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
