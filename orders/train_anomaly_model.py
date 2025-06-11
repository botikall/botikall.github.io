import joblib
from sklearn.ensemble import IsolationForest
import pandas as pd
from datetime import timedelta
from .models import ActionLog  # або from your_app.models import ActionLog

MODEL_PATH = 'media/ml_models/isolation_forest_model.pkl'

def get_training_data():
    logs = ActionLog.objects.order_by('-timestamp')[:1000]
    data = []

    for log in logs:
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

        data.append({
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
        })

    return pd.DataFrame(data)

def train_and_save_model():
    df = get_training_data()
    if len(df) < 10:
        print("Недостатньо даних для тренування")
        return

    features = df[[
        "user_id", "user_type", "action", "object_id",
        "model_len", "desc_len", "ip_present", "ip_is_new",
        "hour_of_day", "action_frequency", "time_since_last_action"
    ]]

    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(features)

    import os
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print("✅ Модель збережена у", MODEL_PATH)

# Запускай як скрипт або через Django management command
if __name__ == "__main__":
    train_and_save_model()
