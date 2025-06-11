# /generate_monthly_sales.py
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.db.models import Sum
from orders.models import OrderItem  # заміни на правильний шлях
from .models import MonthlyProductSales

import datetime

def run_monthly_sales_report():
    Command().handle()

class Command(BaseCommand):
    help = 'Генерує місячну статистику продажів продуктів'

    def handle(self, *args, **kwargs):
        today = now().date()
        first_day = today.replace(day=1)
        previous_month = first_day - datetime.timedelta(days=1)
        month_start = previous_month.replace(day=1)
        month_end = previous_month.replace(day=1) + datetime.timedelta(days=31)
        month_end = month_end.replace(day=1) - datetime.timedelta(days=1)

        sales = (
            OrderItem.objects.filter(order__created_at__date__range=(month_start, month_end))
            .values("product__name")
            .annotate(total_quantity=Sum("quantity"))
        )

        for item in sales:
            MonthlyProductSales.objects.update_or_create(
                product_name=item["product__name"],
                month=month_start,
                defaults={"total_quantity": item["total_quantity"]}
            )

        self.stdout.write(self.style.SUCCESS(f"✅ Продажі за {month_start.strftime('%B %Y')} збережено."))
