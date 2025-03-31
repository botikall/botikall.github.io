from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, EditProfileForm
from .models import Product, Cart, CartItem, Order, OrderItem,CustomUser
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CommentForm,ContactForm
from .models import Notification
from .models import Comment,ContactMessage,Type
from django.urls import reverse
from django.db.models import Sum

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')) \
        .order_by('-total_sold')
    # Додаємо поле з продажами після сортування, щоб не втрачати його
    has_purchased = OrderItem.objects.filter(order__user=request.user, product=product, status='completed').exists()

    return render(request, 'orders/product_detail.html', {'product': product,'products': products, 'has_purchased': has_purchased})

def navbar_data(request):
    types = Type.objects.all()
    return {"product_types": types}

def product_catalog(request, type_name=None):
    sort_by = request.GET.get("sort", "default")

    if type_name:
        product_type = get_object_or_404(Type, name=type_name)
        products = Product.objects.filter(type=product_type)
    else:
        products = Product.objects.all()

    # Сортування
    if sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "newest":
        products = products.order_by("-created_at")  # Сортуємо по новизні

    # Додаємо поле з продажами після сортування, щоб не втрачати його
    for product in products:
        product.sales_count = product.get_sales_count()

    types = Type.objects.all()

    return render(request, 'orders/catalog.html', {
        'products': products,
        'types': types,
        'selected_type': type_name,
        'sort_by': sort_by
    })

def check_join_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({"redirect_url": "/login/"})  # Перенаправлення на сторінку входу
    return JsonResponse({"message": "Ви вже приєдналися до нашої спільноти!"})

@csrf_exempt
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')

    notifications_list = [
        {'id': n.id, 'message': n.message, 'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')}
        for n in notifications
    ]

    print("Сповіщень знайдено:", len(notifications_list))  # Додаємо логування

    return JsonResponse({'notifications': notifications_list})

@login_required
def add_comment(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Замовлення не знайдено."})

        # Перевіряємо, чи вже є коментар для цього замовлення
        if Comment.objects.filter(order=order).exists():
            return JsonResponse({"success": False, "error": "Ви вже оцінювали це замовлення."})

        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.order = order
            comment.save()
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": f"Помилка валідації: {form.errors}"})

    return JsonResponse({"success": False, "error": "Невірний метод запиту"})


def view_comment(request):
    if request.method == "POST":
        form = ContactForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.user = request.user
                contact_message.name = request.user.get_full_name()
                contact_message.email = request.user.email
            contact_message.save()
            return redirect('comments')
    else:
        form = ContactForm(user=request.user if request.user.is_authenticated else None)

    comments = Comment.objects.all().order_by('-created_at')
    return render(request, 'orders/comments.html', {'form': form,'comments': comments})

def notifications_view(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    else:
        notifications = []
    return {'notifications': notifications}

def admin_order_list(request):
    messages = ContactMessage.objects.all().order_by('-created_at')
    orders = Order.objects.all()
    return render(request, 'orders/admin_form.html', {'orders': orders, 'messages': messages})


@csrf_exempt
def update_order_status(request, order_id, new_status):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id)
        order.status = new_status
        order.save()

        # Створюємо сповіщення для користувача, якщо замовлення виконано
        if new_status == "completed":
            Notification.objects.create(
                user=order.user,
                message=f"Ваше замовлення №{order.id} виконано!"
            )

        return JsonResponse({"success": True, "new_status": order.get_status_display()})
    return JsonResponse({"success": False})

def get_text(request):
    data = {
        'message': 'Додайте хоч елемент один в кошик.'
    }
    return JsonResponse(data)

@csrf_exempt
def cancel_order(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status not in ['completed', 'canceled']:  # Перевірка, чи можна скасувати
            order.status = 'canceled'
            order.save()
            return JsonResponse({"success": True, "status": "Скасований"})
        return JsonResponse({"success": False, "error": "Замовлення вже завершене або скасоване."})
    return JsonResponse({"success": False, "error": "Невірний метод запиту."}, status=400)

# Головна сторінка
def index(request):
    if request.method == "POST":
        form = ContactForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.user = request.user
                contact_message.name = request.user.get_full_name()
                contact_message.email = request.user.email
            contact_message.save()
            return redirect('index')
    else:
        form = ContactForm(user=request.user if request.user.is_authenticated else None)

    total_orders = Order.objects.count()
    total_users = CustomUser.objects.count()
    orders = Order.objects.all()
    products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')) \
                   .order_by('-total_sold')
    # Додаємо поле з продажами після сортування, щоб не втрачати його
    for product in products:
        product.sales_count = product.get_sales_count()

    comments = Comment.objects.order_by('-id')[:4]
    return render(request, 'orders/index.html', {'products': products, 'comments': comments, 'orders': orders,"total_orders": total_orders,
        "total_users": total_users,'form': form})


@login_required
def comments_view(request):
    comments = Comment.objects.all().order_by('-id')
    return render(request, 'orders/comments.html', {'comments': comments})


# Відображення списку продуктів
def product_list(request):
    products = Product.objects.all()
    return render(request, 'orders/product_list.html', {'products': products})


# Реєстрація користувача
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація пройшла успішно!')
            return redirect('index')
        else:
            messages.error(request, 'Помилка реєстрації. Перевірте дані форми.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'orders/register.html', {'form': form})


# Перегляд профілю користувача
@login_required(login_url='login')
def user_profile(request):
    if request.user.is_superuser:
        return redirect('admin_form')  # Перенаправлення для суперкористувача

    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('user_profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = EditProfileForm(instance=user)

    products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')) \
        .order_by('-total_sold')
    return render(request, 'orders/profile.html', {'products': products, 'form': form, 'orders': orders})

@login_required
def admin_form(request):
    return render(request, 'orders/admin_form.html')

# Редагування профілю користувача
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('user_profile')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'orders/edit_profile.html', {'form': form})


# Зміна пароля
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успішно змінено.')
            return redirect('user_profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки.')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'orders/change_password.html', {'form': form})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    quantity = request.POST.get('quantity', 1)

    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if created:
        cart_item.quantity = quantity  # Встановлюємо кількість при створенні нового запису
    else:
        cart_item.quantity += quantity  # Додаємо кількість, якщо товар уже є в кошику

    cart_item.save()
    messages.success(request, f'{product.name} у кількості {quantity} шт. було додано до кошика.')

    # Повертаємо JSON-відповідь для Ajax-запиту
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "redirect_url": request.build_absolute_uri(reverse('cart'))})

    return redirect('order_form')


# Видалення елемента з кошика
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Елемент видалено з кошика.')
    return redirect('order_form')


# Оновлення кількості елементів у кошику
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        new_quantity = request.POST.get('quantity', 1)
        cart_item.quantity = int(new_quantity)
        cart_item.save()
        messages.success(request, 'Кількість елементів оновлено.')
    return redirect('order_form')


# Відображення кошика
@login_required(login_url='login')
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_items = cart.items.all()
    total_price = cart.get_total_price()

    return render(request, 'orders/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    })

# Оформлення замовлення
@login_required(login_url='login')
def order_form(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.error(request, 'Ваш кошик порожній.')
        return redirect('product_catalog')

    if request.method == 'POST':
        delivery_type = request.POST.get('delivery_type')
        delivery_address = request.POST.get('delivery_address') if delivery_type == 'courier' else None
        latitude = request.POST.get('latitude') if delivery_type == 'courier' else None
        longitude = request.POST.get('longitude') if delivery_type == 'courier' else None

        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total_price(),
            delivery_type=delivery_type,
            delivery_address=delivery_address,
            latitude=latitude,
            longitude=longitude
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.get_total_price()
            )

        cart.items.all().delete()
        messages.success(request, 'Замовлення успішно оформлено!')
        return redirect('order_success')

    products = Product.objects.annotate(total_sold=Sum('orderitem__quantity')) \
        .order_by('-total_sold')
    total_price = cart.get_total_price()
    return render(request, 'orders/order_form.html', {
        'cart': cart,
        'total_price': total_price,
        'products': products
    })

# Сторінка успішного замовлення
@login_required
def order_success(request):
    return render(request, 'orders/order_success.html')

@login_required
def add_comment_for_product(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        has_purchased = OrderItem.objects.filter(order__user=request.user, product=product, status='completed').exists()

        if not has_purchased:
            return JsonResponse(
                {"success": False, "error": "Ви не можете залишити коментар, оскільки не купували цей товар."})

        if CommentForProduct.objects.filter(user=request.user, product=product).exists():
            return JsonResponse({"success": False, "error": "Ви вже залишали коментар для цього товару."})

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.product = product
            comment.save()
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": f"Помилка валідації: {form.errors}"})

    return JsonResponse({"success": False, "error": "Невірний метод запиту"})