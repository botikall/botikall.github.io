from django.contrib import admin

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

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(Type)
admin.site.register(CommentForProduct)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "real_name", "first_name", "last_name")
    search_fields = ("username", "email", "real_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
