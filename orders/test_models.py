import pytest
from django.contrib.auth import get_user_model
from orders.models import Cart, CartItem, Product

@pytest.mark.django_db
def test_add_to_cart():
    # Створюємо продукт
    product = Product.objects.create(
        name="Тестовий продукт",
        price=50.0
    )

    # Створюємо користувача
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="testuser",
        password="test123"
    )

    # Створюємо кошик
    cart = Cart.objects.create(user=user)

    # Додаємо елемент до кошика
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2
    )

    # Перевіряємо, що елемент доданий
    assert cart.items.count() == 1
    item = cart.items.first()
    assert item.product == product
    assert item.quantity == 2
    assert item.get_total_price() == 100.0  # 50.0 * 2


@pytest.mark.django_db
def test_calculate_total():
    # Створюємо користувача
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="testuser",
        password="test123"
    )

    # Створюємо кошик
    cart = Cart.objects.create(user=user)

    # Створюємо продукти
    product1 = Product.objects.create(name="Продукт 1", price=50.0)
    product2 = Product.objects.create(name="Продукт 2", price=30.0)

    # Додаємо елементи до кошика
    CartItem.objects.create(cart=cart, product=product1, quantity=2)
    CartItem.objects.create(cart=cart, product=product2, quantity=3)

    # Перевіряємо загальну суму через метод моделі Cart
    assert cart.get_total_price() == 190.0  # (50.0 * 2) + (30.0 * 3)
