import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


class MonthlyProductSales(models.Model):
    product_name = models.CharField(max_length=255)
    total_quantity = models.PositiveIntegerField()
    month = models.DateField()  # Наприклад, 2025-06-01 для червня

    class Meta:
        unique_together = ('product_name', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.product_name} – {self.month.strftime('%B %Y')}"


class ProductSalesReport(models.Model):
    last_graf = models.DateTimeField()

    def __str__(self):
        return f"Оновлення: {self.last_graf}"

class AnomalyModelTraining(models.Model):
    last_trained = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Останнє тренування: {self.last_trained.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = "Модель аномалії"
        verbose_name_plural = "Модель аномалії"

class ActionLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Створення'),
        ('update', 'Оновлення'),
        ('delete', 'Видалення'),
        ('login', 'Вхід'),
        ('logout', 'Вихід'),
        ('get', 'Отримання'),
        ('add', 'Додавання'),
        ('view', 'Перегляд'),
        ('custom', 'Інше'),
        ('cancel', 'Відмова'),
    ]

    ACTION_CODE_MAP = {
        'create': 1, 'update': 2, 'delete': 3,
        'login': 4, 'logout': 5, 'get': 6,
        'add': 7, 'view': 8, 'custom': 9,'cancel': 10,
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_code = models.PositiveSmallIntegerField(default=0)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    ip_country = models.CharField(max_length=5, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.action_code = self.ACTION_CODE_MAP.get(self.action, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {self.user} | {self.action} | {self.model_name}({self.object_id})"

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["action"]),
        ]

class AnomalyEvent(models.Model):
    action_log = models.OneToOneField(ActionLog, on_delete=models.CASCADE, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)
    is_anomaly = models.BooleanField()
    score = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Anomaly: {self.action_log} | Score: {self.score:.4f}"


class ContactMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        if self.user:
            return f"Сповіщення для {self.user.username} - {self.message}"
        elif self.session_key:
            return f"Сповіщення для сесії {self.session_key} - {self.message}"
        else:
            return f"Сповіщення (невідомий користувач) - {self.message}"


# Модель користувача
class CustomUser(AbstractUser):
    real_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)


class Type(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Тип продукту")
    image = models.ImageField(
        upload_to="category_images/",
        blank=True,
        null=True,
        verbose_name="Зображення категорії",
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва продукту")
    description = models.TextField(verbose_name="Опис продукту", blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна продукту"
    )
    image = models.ImageField(
        upload_to="products/", blank=True, null=True, verbose_name="Зображення продукту"
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Тип продукту",
    )
    created_at = models.DateTimeField(default=now, verbose_name="Дата додавання")
    composition = models.TextField(verbose_name="Склад продукту", blank=True)
    weight = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Вага продукту (г)",
        blank=True,
        null=True,
    )
    article = models.CharField(
        max_length=50, verbose_name="Артикул", blank=True, null=True
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.article:  # Генеруємо артикул, якщо його немає
            unique_id = (
                uuid.uuid4().hex[:8].upper()
            )  # Генеруємо 8-значний унікальний код
            self.article = f"PRD-{unique_id}"
        super().save(*args, **kwargs)

    def get_sales_count(self):
        from .models import OrderItem  # Імпорт тут, щоб уникнути циклічних імпортів

        sales = OrderItem.objects.filter(product=self, status="completed").aggregate(
            Sum("quantity")
        )
        return sales["quantity__sum"] or 0  # Якщо немає продажів, повертаємо 0


# Модель кошика
class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кошик {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())


# Модель елемента в кошику
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# Модель замовлення
class Order(models.Model):
    """
    Модель замовлення, яка зберігає дані про замовника, оплату та товари.
    """

    STATUS_CHOICES = [
        ("new", "Нове"),
        ("processing", "В обробці"),
        ("completed", "Завершено"),
        ("canceled", "Скасовано"),
    ]

    DELIVERY_CHOICES = [("pickup", "Самовивіз"), ("courier", "Доставка кур'єром")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Користувач",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус замовлення",
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, verbose_name="Загальна сума"
    )
    delivery_type = models.CharField(
        max_length=10,
        choices=DELIVERY_CHOICES,
        default="pickup",
        verbose_name="Спосіб доставки",
    )
    delivery_address = models.TextField(
        null=True, blank=True, verbose_name="Адреса доставки"
    )
    latitude = models.FloatField(null=True, blank=True, verbose_name="Широта")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Довгота")

    def __str__(self):
        """
        Повертає рядкове представлення замовлення.
        """

        return f"Замовлення {self.id} - {self.user.username} - {self.status}"

    def update_status(self):
        """
        Оновлює статус замовлення залежно від статусів OrderItem.
        """

        items = self.items.all()

        if items.exists():
            if all(item.status == "completed" for item in items):
                self.status = "completed"
            elif any(item.status == "completed" for item in items):
                self.status = "processing"
            else:
                self.status = "new"

            self.save()

    def save(self, *args, **kwargs):
        """
        Оновлює статус усіх OrderItem, якщо замовлення стало 'completed'.
        """

        super().save(*args, **kwargs)

        if self.status == "completed":
            self.items.update(status="completed")


@receiver(post_save, sender=Order)
def create_notification(sender, instance, **kwargs):
    """
    Створює сповіщення, коли замовлення завершується.
    """

    if instance.status == "completed":
        Notification.objects.create(
            user=instance.user, message=f"Ваше замовлення #{instance.id} завершено!"
        )


# Модель елемента в замовленні з власним статусом виконання
class OrderItem(models.Model):
    STATUS_CHOICES = [
        ("new", "Нове"),
        ("processing", "В обробці"),
        ("completed", "Завершено"),
        ("canceled", "Скасовано"),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Замовлення"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Продукт"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Статус товару",
    )

    def __str__(self):
        return f"{self.quantity} x {self.product.name} у замовленні {self.order.id} - {self.status}"

    def save(self, *args, **kwargs):
        """Оновлює статус замовлення після зміни статусу товару."""
        super().save(*args, **kwargs)
        self.order.update_status()


class Comment(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE
    )  # Один коментар до одного замовлення
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], default=5
    )  # Оцінка від 1 до 5
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.order.user.username} - {self.rating}★"


class CommentForProduct(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Продукт",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="CommentForProduct",
        verbose_name="Користувач",
        default=1,
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    text = models.TextField(verbose_name="Текст коментаря")
    created_at = models.DateTimeField(default=now, verbose_name="Дата додавання")

    def clean(self):
        if len(self.text) > 50:
            raise ValidationError("Коментар не може містити більше ніж 50 символів.")

    def __str__(self):
        return f"Comment by {self.user.username} - {self.rating}★"
