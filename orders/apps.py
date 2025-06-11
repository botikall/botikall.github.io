from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        if not scheduler.running:
            from .anomaly_detector import detect_last_log_anomaly
            scheduler.add_job(detect_last_log_anomaly, 'interval', days=1)
            from .generate_monthly_sales import run_monthly_sales_report
            scheduler.add_job(run_monthly_sales_report, 'cron', day=1, hour=0, minute=0)
            scheduler.start()