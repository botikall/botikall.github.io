
from .models import (
    Cart,
    CartItem,
    Comment,
    CommentForProduct,
    CustomUser,
    Notification,
    Order,
    OrderItem,
    Product,
    Type,
)
from django.contrib import admin
from .models import AnomalyEvent

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(Type)
admin.site.register(CommentForProduct)

from django.urls import reverse
from django.utils.html import format_html
import json
from .models import ActionLog,AnomalyModelTraining,ProductSalesReport
from .train_anomaly_model import train_and_save_model
from django.shortcuts import redirect
from django.contrib import messages
import datetime
from django.contrib import admin
from django.urls import path
from django.db.models import Sum
from django.shortcuts import render
from .models import MonthlyProductSales

@admin.register(MonthlyProductSales)
class MonthlyProductSalesAdmin(admin.ModelAdmin):
    list_display = ("product_name", "month", "total_quantity")
    list_filter = ("month",)
    search_fields = ("product_name",)

@admin.register(ProductSalesReport)
class ProductSalesAdmin(admin.ModelAdmin):
    change_list_template = "admin/product_sales_chart.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "sales-stats/",
                self.admin_site.admin_view(self.sales_stats),
                name="orders_productsalesreport_sales_stats",  # <-- ВАЖЛИВО
            )
        ]
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['sales_stats_url'] = reverse('admin:orders_productsalesreport_sales_stats')
        return super().changelist_view(request, extra_context=extra_context)

    def sales_stats(self, request):
        from django.utils.timezone import now
        today = now().date()
        month_ago = today - datetime.timedelta(days=30)

        sales = (
            OrderItem.objects.filter(
                order__created_at__gte=month_ago,
                status="completed",
            )
            .values("product__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")
        )

        labels = [item["product__name"] for item in sales]
        data = [item["total_quantity"] for item in sales]

        # Отримуємо останній час оновлення, наприклад, з моделі ProductSalesReport або теперішній час
        from django.utils.timezone import now
        try:
            last_report = ProductSalesReport.objects.latest("last_graf")
            last_graf_time = last_report.last_graf
        except ProductSalesReport.DoesNotExist:
            last_graf_time = now()

        context = dict(
            self.admin_site.each_context(request),
            labels=json.dumps(labels),
            data=json.dumps(data),
            last_graf=last_graf_time,
        )
        return render(request, "admin/product_sales_chart.html", context)



@admin.register(AnomalyModelTraining)
class AnomalyModelTrainingAdmin(admin.ModelAdmin):
    change_list_template = "admin/anomaly_model_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('train/', self.admin_site.admin_view(self.train_model), name='train-anomaly-model'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        last_train = AnomalyModelTraining.objects.first()
        extra_context = extra_context or {}
        extra_context['last_trained'] = last_train.last_trained if last_train else None
        return super().changelist_view(request, extra_context=extra_context)

    def train_model(self, request):
        train_and_save_model()
        AnomalyModelTraining.objects.update_or_create(id=1, defaults={})
        self.message_user(request, "Модель аномалії успішно оновлено ✅", messages.SUCCESS)
        return redirect("..")

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address')
    search_fields = ('user__username', 'model_name', 'object_id', 'description')
    list_filter = ('action', 'model_name', 'timestamp')
    readonly_fields = [f.name for f in ActionLog._meta.fields]

@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ('action_log', 'detected_at', 'is_anomaly', 'score', 'view_graph_link')

    def view_graph_link(self, obj):
        url = reverse('anomaly_graph')
        return format_html('<a href="{}">📈 Переглянути графік</a>', url)

    view_graph_link.short_description = 'Графік'

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "real_name", "first_name", "last_name")
    search_fields = ("username", "email", "real_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
