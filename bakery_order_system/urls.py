from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, include
import debug_toolbar
from orders.views import CustomLoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from orders import views  # Імпортуємо всі представлення з модуля orders
from orders.views import (
    add_comment,
    add_comment_for_product,
    cancel_order,
    check_join_status,
    edit_profile,
    get_notifications,
    mark_notification_read,
    product_catalog,
    product_detail,
    update_order_status,
    user_profile,
    view_comment,
)
from orders.views import ProtectedDataView

urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/protected/", ProtectedDataView.as_view(), name="protected_data"),
    path('anomalies/graph/', views.anomaly_graph_view, name='anomaly_graph'),
    path('__debug__/', include(debug_toolbar.urls)),
    path("product/<int:product_id>/", product_detail, name="product_detail"),
    path("catalog/", product_catalog, name="product_catalog"),
    path("catalog/<str:type_name>/", product_catalog, name="product_by_type"),
    path("join-check/", check_join_status, name="join_check"),
    path("orders/cancel/<int:order_id>/", cancel_order, name="cancel_order"),
    path(
        "add_comment_for_product/",
        add_comment_for_product,
        name="add_comment_for_product",
    ),
    path("add_comment/", add_comment, name="add_comment"),
    path("comments/", view_comment, name="comments"),
    path("get-notifications/", get_notifications, name="get_notifications"),
    path(
        "mark-notification-read/<int:notification_id>/",
        mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "update-order-status/<int:order_id>/<str:new_status>/",
        update_order_status,
        name="update_order_status",
    ),
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("products/", views.product_list, name="product_list"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    # path("order/success/", views.order_success, name="order_success"),
    path("order/", views.order_form, name="order_form"),
    path("login/special", CustomLoginView.as_view(template_name="orders/login.html", redirect_authenticated_user=True), name="login_special"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="orders/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page="index"), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", user_profile, name="user_profile"),
    path("profile/edit/", edit_profile, name="edit_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    path("checkout/", views.order_form, name="checkout"),
    path("get_text/", views.get_text, name="get_text"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
