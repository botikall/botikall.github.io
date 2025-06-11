from django.contrib import messages
from functools import wraps
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.decorators import method_decorator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .forms import UkrainianPasswordChangeForm

from .forms import CommentForm, ContactForm, CustomUserCreationForm, EditProfileForm
from .models import (
    Cart,
    CartItem,
    Comment,
    CommentForProduct,
    ContactMessage,
    CustomUser,
    Notification,
    Order,
    OrderItem,
    Product,
    Type,
)

from .logging import log_action

from .anomaly_detector import detect_last_log_anomaly
import logging
from .models import AnomalyEvent
from django.contrib.auth.views import LoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class ProtectedDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Привіт, {request.user.username}! Це захищені дані."})

logger = logging.getLogger("django")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

# def login_required_with_temp_notification(view_func):
#     @wraps(view_func)
#     def _wrapped_view(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             if not request.session.session_key:
#                 request.session.save()
#
#             Notification.objects.create(
#                 session_key=request.session.session_key,
#                 message="Спочатку авторизуйтесь."
#             )
#
#             login_url = reverse("login")
#             return redirect(f"{login_url}?next={request.path}")
#
#         return view_func(request, *args, **kwargs)
#
#     return _wrapped_view

def anomaly_graph_view(request):
    events = AnomalyEvent.objects.order_by('detected_at')
    labels = [e.detected_at.strftime("%Y-%m-%d %H:%M:%S") for e in events]
    scores = [e.score for e in events]
    colors = ['red' if e.is_anomaly else 'green' for e in events]

    context = {
        'labels': labels,
        'scores': scores,
        'colors': colors
    }
    return render(request, 'admin/graph.html', context)

def anomaly_check_view(request):
    result = detect_last_log_anomaly()
    return JsonResponse(result)

class CustomLoginView(LoginView):
    template_name = "orders/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        session_key = self.request.session.session_key
        log_action(self.request, "login", "Успішний вхід користувача")
        if session_key:
            Notification.objects.filter(
                session_key=session_key,
                user__isnull=True
            ).update(user=self.request.user, session_key=None)

        return self.get_redirect_url() or reverse("index")

def product_detail(request, product_id):
    log_action(request, "view", "Product", object_id=product_id, description="Перегляд продукту")
    product = get_object_or_404(Product, id=product_id)
    comments = CommentForProduct.objects.filter(product=product).order_by("-created_at")
    products = Product.objects.annotate(total_sold=Sum("orderitem__quantity")).order_by("-total_sold")

    has_purchased = False
    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user, product=product, status="completed"
        ).exists()

    return render(
        request,
        "orders/product_detail.html",
        {
            "product": product,
            "products": products,
            "has_purchased": has_purchased,
            "comments": comments,
        },
    )


def navbar_data(request):
    types = Type.objects.all()
    return {"product_types": types}


def product_catalog(request, type_name=None):
    log_action(request, "view", "Product", object_id=type_name, description="Перегляд каталогу")
    cart = None
    total_price = 0

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        total_price = cart.get_total_price()

    sort_by = request.GET.get("sort", "default")

    if type_name:
        product_type = get_object_or_404(Type, name=type_name)
        products = Product.objects.filter(type=product_type)
    else:
        products = Product.objects.all()

    if sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "newest":
        products = products.order_by("-created_at")

    for product in products:
        product.sales_count = product.get_sales_count()

    types = Type.objects.all()

    return render(
        request,
        "orders/catalog.html",
        {
            "cart": cart,
            "total_price": total_price,
            "products": products,
            "types": types,
            "selected_type": type_name,
            "sort_by": sort_by,
        },
    )


def check_join_status(request):
    log_action(request, "view", description="Перевірка статусу приєднання")
    if not request.user.is_authenticated:
        return JsonResponse(
            {"redirect_url": "/login/"}
        )
    return JsonResponse({"message": "Ви вже приєдналися до нашої спільноти!"})


@csrf_exempt
def mark_notification_read(request, notification_id):
    log_action(request, "view", "Notification", object_id=notification_id, description="Переглянуте сповіщення")
    if request.method == "POST":
        notification = get_object_or_404(
            Notification, id=notification_id, user=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


def get_notifications(request):
    # log_action(request, "get","Notification", description="Отримання сповіщення")
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            user=request.user, is_read=False
        )
    else:
        if not request.session.session_key:
            request.session.save()

        notifications = Notification.objects.filter(
            session_key=request.session.session_key, is_read=False
        )

    notifications = notifications.order_by("-created_at")

    notifications_list = [
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for n in notifications
    ]

    print("Сповіщень знайдено:", len(notifications_list))

    return JsonResponse({"notifications": notifications_list})

@login_required
def add_comment(request):
    log_action(request, "add","Comment", description="Додавання коментаря")
    if request.method == "POST":
        order_id = request.POST.get("order_id")

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Замовлення не знайдено."})


        if Comment.objects.filter(order=order).exists():
            return JsonResponse(
                {"success": False, "error": "Ви вже оцінювали це замовлення."}
            )

        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.order = order
            comment.save()
            return JsonResponse({"success": True})

        return JsonResponse(
            {"success": False, "error": f"Помилка валідації: {form.errors}"}
        )

    return JsonResponse({"success": False, "error": "Невірний метод запиту"})


def view_comment(request):
    log_action(request, "view","Comment", description="Перегляд коментаря")
    if request.method == "POST":
        form = ContactForm(
            request.POST, user=request.user if request.user.is_authenticated else None
        )
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.user = request.user
                contact_message.name = request.user.get_full_name()
                contact_message.email = request.user.email
            contact_message.save()
            return redirect("comments")
    else:
        form = ContactForm(user=request.user if request.user.is_authenticated else None)

    comments = Comment.objects.all().order_by("-created_at")
    return render(request, "orders/comments.html", {"form": form, "comments": comments})


def notifications_view(request):
    log_action(request, "view","Notification", description="Перегляд сповіщень")
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            user=request.user, is_read=False
        ).order_by("-created_at")
    else:
        notifications = []
    return {"notifications": notifications}



@csrf_exempt
def update_order_status(request, order_id, new_status):
    log_action(request, "update", "Notification", object_id=order_id, description="Оновлення статусу")
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()

        # Створюємо сповіщення для користувача, якщо замовлення виконано
        if new_status == "completed":
            Notification.objects.create(
                user=order.user, message=f"Ваше замовлення №{order.id} виконано!"
            )

        return JsonResponse({"success": True, "new_status": order.get_status_display()})
    return JsonResponse({"success": False})


def get_text(request):
    log_action(request, "get","text", description="Отримання тексту")
    data = {"message": "Додайте хоч елемент один в кошик."}
    return JsonResponse(data)


@csrf_exempt
def cancel_order(request, order_id):
    log_action(request, "cancel", "Order", object_id=order_id, description="Відмова від замовлення")
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status not in [
            "completed",
            "canceled",
        ]:  # Перевірка, чи можна скасувати
            order.status = "canceled"
            order.save()
            return JsonResponse({"success": True, "status": "Скасований"})
        return JsonResponse(
            {"success": False, "error": "Замовлення вже завершене або скасоване."}
        )
    return JsonResponse(
        {"success": False, "error": "Невірний метод запиту."}, status=400
    )

def index(request):
    log_action(request, "view", "Form", description="Перегляд головної сторінки")
    if request.method == "POST":
        form = ContactForm(
            request.POST, user=request.user if request.user.is_authenticated else None
        )
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.user = request.user
                contact_message.name = request.user.get_full_name()
                contact_message.email = request.user.email
            contact_message.save()
            return redirect("index")
    else:
        form = ContactForm(user=request.user if request.user.is_authenticated else None)

    total_orders = Order.objects.count()
    total_users = CustomUser.objects.count()
    orders = Order.objects.all()
    products = Product.objects.annotate(total_sold=Sum("orderitem__quantity")).order_by(
        "-total_sold"
    )
    # Додаємо поле з продажами після сортування, щоб не втрачати його
    for product in products:
        product.sales_count = product.get_sales_count()

    comments = Comment.objects.order_by("-id")[:4]
    return render(
        request,
        "orders/index.html",
        {
            "products": products,
            "comments": comments,
            "orders": orders,
            "total_orders": total_orders,
            "total_users": total_users,
            "form": form,
        },
    )


@login_required
def comments_view(request):
    log_action(request, "view","Comment", description="Перегляд коментарів")
    comments = Comment.objects.all().order_by("-id")
    return render(request, "orders/comments.html", {"comments": comments})


def product_list(request):
    log_action(request, "view","Product", description="Перегляд продукції")
    products = Product.objects.all()
    return render(request, "orders/product_list.html", {"products": products})


def register(request):
    log_action(request, "register","Form", description="Реєстрація користувача")
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Реєстрація пройшла успішно!")
            return redirect("index")
        else:
            messages.error(request, "Помилка реєстрації. Перевірте дані форми.")
    else:
        form = CustomUserCreationForm()
    return render(request, "orders/register.html", {"form": form})


@login_required(login_url="login")
def user_profile(request):
    log_action(request, "view","Form", description="Перегляд профілю")
    if request.user.is_superuser:
        return redirect(reverse("admin:index")) # Перенаправлення для суперкористувача

    user = request.user
    orders = Order.objects.filter(user=user).order_by("-created_at")

    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль успішно оновлено.")
            return redirect("user_profile")
        else:
            messages.error(request, "Будь ласка, виправте помилки у формі.")
    else:
        form = EditProfileForm(instance=user)

    products = Product.objects.annotate(total_sold=Sum("orderitem__quantity")).order_by(
        "-total_sold"
    )
    return render(
        request,
        "orders/profile.html",
        {"products": products, "form": form, "orders": orders},
    )

# Редагування профілю користувача
@login_required
def edit_profile(request):
    log_action(request, "update","Form", description="Зміна данних профілю")
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль успішно оновлено.")
            return redirect("user_profile")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "orders/edit_profile.html", {"form": form})


# Зміна пароля
@login_required
def change_password(request):
    log_action(request, "update","Form", description="Зміна паролю")
    if request.method == "POST":
        form = UkrainianPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль успішно змінено.")
            return redirect("user_profile")
        else:
            messages.error(request, "Будь ласка, виправте помилки.")
    else:
        form = UkrainianPasswordChangeForm(user=request.user)

    return render(request, "orders/change_password.html", {"form": form})


@login_required
def add_to_cart(request, product_id):
    log_action(request, "add","Product",object_id=product_id, description="Додавання елементів до кошика")
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    quantity = request.POST.get("quantity", 1)

    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        cart_item.quantity = (
            quantity  # Встановлюємо кількість при створенні нового запису
        )
    else:
        cart_item.quantity += quantity  # Додаємо кількість, якщо товар уже є в кошику

    cart_item.save()
    messages.success(
        request, f"{product.name} у кількості {quantity} шт. було додано до кошика."
    )

    # Повертаємо JSON-відповідь для Ajax-запиту
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "redirect_url": request.build_absolute_uri(reverse("cart")),
            }
        )

    return redirect("product_catalog")


@login_required
def remove_from_cart(request, item_id):
    log_action(request, "delete", "CartItem", object_id=item_id, description="Видалення елемента з кошика")
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Елемент видалено з кошика.")
    return redirect(request.META.get('HTTP_REFERER', 'order_form'))

@login_required
def clear_cart(request):
    log_action(request, "clear","CartItem", description="Повне очищення кошика")
    request.user.cart.items.all().delete()
    messages.success(request, "Кошик очищено.")
    return redirect(request.META.get('HTTP_REFERER', 'order_form'))


@login_required
def update_cart_item(request, item_id):
    log_action(request, "update","CartItem", object_id=item_id, description="Змінення кількості продукції")
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        new_quantity = request.POST.get("quantity", 1)
        cart_item.quantity = int(new_quantity)
        cart_item.save()
        messages.success(request, "Кількість елементів оновлено.")
    return redirect("order_form")


@login_required(login_url="login")
def order_form(request):
    log_action(request, "create","Cart", description="Створення замовлення")
    cart, created = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if not cart.items.exists():
            return render(
                request,
                "orders/order_form.html",
                {
                    "cart": cart,
                    "total_price": 0,
                    "products": [],
                    "error": "Кошик порожній. Додайте товари, щоб оформити замовлення."
                },
            )

        delivery_type = request.POST.get("delivery_type")
        delivery_address = (
            request.POST.get("delivery_address") if delivery_type == "courier" else None
        )
        latitude = request.POST.get("latitude") if delivery_type == "courier" else None
        longitude = (
            request.POST.get("longitude") if delivery_type == "courier" else None
        )

        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price(),
            delivery_type=delivery_type,
            delivery_address=delivery_address,
            latitude=latitude,
            longitude=longitude,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.get_total_price(),
            )

        cart.items.all().delete()
        messages.success(request, "Замовлення успішно створено!")
        Notification.objects.create(
            user=request.user,
            message="Замовлення успішно створено!"
        )
        return redirect("order_form")

    products = Product.objects.annotate(total_sold=Sum("orderitem__quantity")).order_by(
        "-total_sold"
    )
    total_price = cart.get_total_price()
    return render(
        request,
        "orders/order_form.html",
        {"cart": cart, "total_price": total_price, "products": products},
    )


# # Сторінка успішного замовлення
# @login_required
# def order_success(request):
#     Notification.objects.create(
#         user=request.user,
#         message="Замовлення успішно створено."
#     )
#     return render(request, "orders/order_form.html")


@login_required
def add_comment_for_product(request):
    log_action(request, "add","Comment", description="Додавання коментаря")
    if request.method == "POST":
        user = request.user
        product_id = request.POST.get("product_id")
        rating = request.POST.get("rating")
        text = request.POST.get("text")

        if len(text) > 50:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Коментар не може містити більше ніж 50 символів.",
                },
                status=400,
            )

        try:
            product = Product.objects.get(id=product_id)
            CommentForProduct.objects.create(
                user=user, product=product, rating=rating, text=text
            )
            return JsonResponse({"success": True})
        except Product.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Продукт не знайдено"}, status=404
            )

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
