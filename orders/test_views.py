import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from orders.models import Cart, CartItem, Order, Product


@pytest.mark.django_db
def test_order_form_view(client):
    user_model = get_user_model()
    user = user_model.objects.create_user(username="testuser", password="test123")
    client.login(username="testuser", password="test123")

    product = Product.objects.create(name="Тестовий продукт", price=50.0)
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=2)

    response = client.post(reverse("checkout"))
    assert response.status_code == 302  # Перевірка перенаправлення

    order = Order.objects.get(user=user)
    assert order.total_price == 100.0
    assert order.items.count() == 1
