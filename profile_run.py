# profile_run.py
import os
import django
from memory_profiler import profile

# 1. Налаштуй Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bakery_order_system.settings")  # або твоя назва проєкту
django.setup()

# 2. Імпортуй усе необхідне
from orders.models import Product  # приклад
# або from orders.views import product_detail — якщо це функція, яку хочеш протестити

@profile
def main():
    try:
        product = Product.objects.get(id=1)
        print(product.name)
    except Product.DoesNotExist:
        print("Продукт з id=1 не існує.")

# 3. Запуск
if __name__ == "__main__":
    main()
