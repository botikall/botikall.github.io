from rest_framework import serializers
from .models import Order, Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image']


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')  # Якщо ви хочете показувати ім'я користувача замість ID

    class Meta:
        model = Order
        fields = ['user', 'created_at', 'total_price']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

    def create(self, validated_data):
        # Якщо потрібно автоматично прив'язувати користувача до замовлення:
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)