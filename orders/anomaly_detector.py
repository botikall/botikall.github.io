import joblib
import os
import pandas as pd
from datetime import timedelta
from .models import AnomalyEvent, ActionLog

MODEL_PATH = 'media/ml_models/isolation_forest_model.pkl'

def extract_features_from_log(log):
    user = log.user
    user_id = user.id if user else 0
    user_type = 1 if user and user.is_superuser else 0
    timestamp = log.timestamp
    hour_of_day = timestamp.hour

    time_window_start = timestamp - timedelta(hours=1)
    recent_logs = ActionLog.objects.filter(user=user, timestamp__gte=time_window_start, timestamp__lte=timestamp)
    action_frequency = recent_logs.count()

    previous_log = ActionLog.objects.filter(user=user, timestamp__lt=timestamp).order_by('-timestamp').first()
    time_since_last_action = (timestamp - previous_log.timestamp).total_seconds() if previous_log else 999999

    ip_present = int(bool(log.ip_address))
    ip_is_new = 0
    if log.ip_address and user:
        used_ips = ActionLog.objects.filter(user=user).exclude(id=log.id).values_list('ip_address', flat=True).distinct()
        ip_is_new = int(log.ip_address not in used_ips)

    return {
        "user_id": user_id,
        "user_type": user_type,
        "action": hash(log.action) % 1000,
        "object_id": int(log.object_id) if log.object_id and str(log.object_id).isdigit() else 0,
        "model_len": len(log.model_name or ""),
        "desc_len": len(log.description or ""),
        "ip_present": ip_present,
        "ip_is_new": ip_is_new,
        "hour_of_day": hour_of_day,
        "action_frequency": action_frequency,
        "time_since_last_action": time_since_last_action,
    }

def detect_last_log_anomaly():
    if not os.path.exists(MODEL_PATH):
        return "Модель аномалій ще не натренована"

    # Завантаження моделі
    model = joblib.load(MODEL_PATH)

    # Отримання останнього запису
    last_log = ActionLog.objects.order_by('-timestamp').first()
    if not last_log:
        return "Немає записів для аналізу"

    # Перевірка наявності вже збереженої аномалії
    if AnomalyEvent.objects.filter(action_log=last_log).exists():
        return "Аномалія вже зареєстрована для цього запису"

    # Витягування ознак
    features_dict = extract_features_from_log(last_log)
    features_df = pd.DataFrame([features_dict])

    # Отримання результату
    score = model.decision_function(features_df)[0]
    is_anomaly = model.predict(features_df)[0] == -1

    if is_anomaly:
        AnomalyEvent.objects.create(
            action_log=last_log,
            is_anomaly=True,
            score=score,
            notes=f"Аномалія для дії {last_log.action} о {last_log.timestamp}"
        )
        return "Аномалію виявлено й збережено"
    else:
        return "Аномалій не виявлено"
