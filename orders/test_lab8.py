import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse

from orders.models import Cart, CartItem, Order, Product


@pytest.mark.django_db
def test_order_form_creates_order(client):
    # Створення тестового користувача
    user_model = get_user_model()
    user = user_model.objects.create_user(username="testuser", password="test123")
    client.login(username="testuser", password="test123")

    # Створення продуктів для кошика
    product = Product.objects.create(name="Тестовий продукт", price=50.0)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)

    # Надсилаємо POST-запит для створення замовлення
    response = client.post(reverse("checkout"))
    assert response.status_code == 302  # Перевірка перенаправлення

    # Перевірка створення замовлення в базі даних
    order = Order.objects.get(user=user)
    assert order.total_price == 100.0
    assert order.items.count() == 1
    assert order.status == "new"


@pytest.mark.django_db
def test_order_invalid_total_price():
    """
    Тест перевіряє, що замовлення з недопустимою сумою викликає ValidationError.
    """
    user_model = get_user_model()
    user = user_model.objects.create_user(username="testuser", password="test123")

    # Очікуємо помилку ValidationError, якщо загальна сума менша за 0.01
    with pytest.raises(ValidationError) as exc_info:
        order = Order(user=user, total_price=0.0)
        order.full_clean()  # Викликаємо перевірку валідаторів вручну перед збереженням

    # Перевіряємо, що текст помилки відповідає очікуваному
    assert "Сума замовлення має бути більшою за 0." in str(exc_info.value)


@pytest.mark.django_db
def test_mock_order_save(client, mocker):
    # Mock для збереження моделі Order
    mock_save = mocker.patch("orders.models.Order.save", autospec=True)

    # Створення тестового користувача
    user_model = get_user_model()
    user = user_model.objects.create_user(username="testuser", password="test123")
    client.login(username="testuser", password="test123")

    # Створення продукту
    product = Product.objects.create(name="Тестовий продукт", price=50.0)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)

    # Виклик функції для оформлення замовлення
    client.post(reverse("checkout"))

    # Перевірка виклику mock_save
    assert mock_save.called
