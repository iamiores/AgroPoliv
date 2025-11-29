from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, CustomAuthenticationForm, QuestionForm, CommentForm
from django.contrib.auth.decorators import login_required
from .models import Article, Item, Kit, Cart, CartItem, KitItem, UsersQuestion, Comment, Service, ServiceOrder, Order, PromoCode, OrderItem, User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from decimal import Decimal
from django.core.mail import send_mail
import json
import random

# Генерація випадкового коду для підтвердження електронної пошти
def generate_code():
    return str(random.randint(100000, 999999))

# Реєстрація користувача з підтвердженням електронної пошти
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)  # витягаємо дані з форми
        email = request.POST.get("email") 
        UserModel = form.Meta.model  # Отримуємо модель користувача з форми

        # якщо email вже існує, показуємо помилку
        if UserModel.objects.filter(email=email).exists():
            form.add_error("email", "This email is already registered.")

        # якщо форма валідна, створюємо користувача
        elif form.is_valid():
            user = form.save(commit=False)  # створюємо користувача, але не зберігаємо в БД
            user.is_verified = False  # позначаємо як непідтвердженого
            user.verification_code = generate_code()  # Генеруємо код підтвердження
            user.save()

            # Надсилаємо код підтвердження на електронну пошту
            send_mail(
                "Verification Code",
                f"Your verification code is: {user.verification_code}",
                "your@gmail.com",
                [user.email],
                fail_silently=False,
            )
            return redirect("verify_email", user_id=user.id)
    else:
        form = CustomUserCreationForm()

    return render(request, "Watering/register.html", {"form": form})

# Підтвердження електронної пошти користувача
def verify_email(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        code = request.POST.get("code")  # отримуємо код з форми

        # Перевіряємо код підтвердження
        if code == user.verification_code:
            user.is_verified = True
            user.verification_code = None
            user.save()
            login(request, user)
            return redirect("home")

        return render(request, "Watering/verify.html", {"error": "Некоректний код підтвердження."})

    return render(request, "Watering/verify.html")

# Вхід користувача
def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(data=request.POST)  # витягаємо дані з форми
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else: 
        form = CustomAuthenticationForm()
    return render(request, "Watering/login.html", {"form": form})

# Вихід користувача
def logout_view(request):
    logout(request)
    return redirect('home')

# Головна сторінка
def home(request):
    return render(request, 'Watering/home.html')

# Сторінка зі статтями
def articles(request):
    articles = Article.objects.all().order_by('-published_date')  # отримуємо всі статті
    question = QuestionForm()  # форма для запитань користувачів
    return render(request, 'Watering/articles.html', {'articles': articles, 'question_form': question})

@login_required
def submit_question(request):  # функція для надсилання питання користувачем
    if request.method == "POST":
        form = QuestionForm(request.POST)  # витягаємо дані з форми
        # Якщо форма валідна, зберігаємо питання
        if form.is_valid():
            UsersQuestion.objects.create(
                user=request.user,
                question_text=form.cleaned_data['question']
            )
            messages.success(request, 'Ваше питання надіслано успішно!')
            return redirect('articles')
        # Інакше кажемо, що користувач дурачок
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = QuestionForm()
    return redirect('articles', {'question_form': form})

# сторінка окремої статті з коментарями
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)  # отримуємо статтю за id
    comments = article.comments.filter(parent__isnull=True).order_by('-created_at')  # отримуємо коментарі до статті
    form = CommentForm()

    return render(request, 'Watering/article_detail.html', {'article': article, 'comments': comments, 'form': form})


@login_required
@csrf_exempt
def add_comment(request, article_id):  # функція для додавання коментаря до статті 
    if request.method == "POST":
        text = request.POST.get('text')  # отримуємо текст коментаря
        parent_id = request.POST.get('parent_id')  # отримуємо id батьківського коментаря (якщо є)

        # якщо користувач вирішив надіслати порожній коментар, кажемо що він дурачок
        if not text.strip():
            return JsonResponse({'error': "Коментар не може бути порожнім."}, status=400)
        
        # створюємо коментар
        article = get_object_or_404(Article, id=article_id)
        comment = Comment.objects.create(
            article=article,
            user=request.user,
            text=text,
            created_at=timezone.now(),
            parent_id=parent_id if parent_id else None
        )

        # повертаємо дані нового коментаря у форматі JSON в AJAX-відповіді
        return JsonResponse({
            'id': comment.id,
            'user': comment.user.username,
            'text': comment.text,
            'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M"),
            'parent_id': comment.parent.id if comment.parent else None
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

# Сторінка каталогу з товарами та наборами
def catalog(request):
    # Фільтри
    category = request.GET.get('category')
    type_filter = request.GET.get('type')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    search = request.GET.get('search', '').strip()

    items = Item.objects.all()
    kits = Kit.objects.all()

    # якщо фільтр категорії застосований, фільтруємо лише одиночні товари за категорією
    if category:
        items = items.filter(category=category)

    # фільтрація за товаром або набором
    if type_filter == 'Item':
        kits = Kit.objects.none()
    elif type_filter == 'Kit':
        items = Item.objects.none()

    # Фільтрація за ціною
    if price_min:
        items = items.filter(price__gte=price_min)
        kits = kits.filter(price__gte=price_min)
    if price_max:
        items = items.filter(price__lte=price_max)
        kits = kits.filter(price__lte=price_max)

    # Пошук за назвою та описом
    if search:
        words = search.split()
        q_objects = Q()
        for word in words:
            q_objects |= Q(name__icontains=word) | Q(description__icontains=word)
        items = items.filter(q_objects)
        kits = kits.filter(q_objects)

    return render(request, 'Watering/catalog.html', {
        'items': items,
        'kits': kits,
    })

# Сторінка окремого товару
def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'Watering/item_detail.html', {'item': item})

# Покупка окремого товару
@login_required
def buy_item(request, item_id):  
    if request.method != "POST":
        return redirect('item_detail', item_id=item_id)
    
    item = get_object_or_404(Item, id=item_id)
    quantity = int(request.POST.get('quantity', '1'))
    promo_code_input = request.POST.get('promo_code', '').strip()

    # перевіряємо чи кількість товару існує на складі
    if quantity > item.quantity:
        messages.error(request, f"На складі доступно лише {item.quantity} одиниць товару.")
        return redirect('item_detail', item_id=item_id)
    
    price = item.price
    discount = Decimal('0')
    promo = None

    # Перевірка промокоду
    if promo_code_input:
        try:
            # Шукаємо активний промокод
            promo = PromoCode.objects.get(code__iexact=promo_code_input, active=True)
            discount = Decimal(promo.discount_percent) / Decimal('100')
        # якщо промокод недійсний або неактивний, кажемо дурачку що він забудьковатий
        except PromoCode.DoesNotExist or not promo.active:
            messages.warning(request, "Промокод недійсний або вже використаний.")
            promo = None
            discount = Decimal('0')

    # Обчислення загальної ціни з урахуванням знижки
    total_price = price * quantity * (Decimal('1.0') - discount)

    # Створення замовлення
    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        promo_code=promo
    )

    # Створення елементів замовлення
    OrderItem.objects.create(
        order=order,
        item=item,
        quantity=quantity,
        price_per_item=price
    )

    # Оновлення кількості товару на складі
    item.quantity -= quantity
    if item.quantity == 0:
        item.in_stock = False
    item.save()

    # Деактивація промокоду після використання
    if promo:
        promo.active = False
        promo.save()

    messages.success(request, f"Ви успішно придбали {quantity} шт. {item.name}")
    return redirect('catalog')


def validate_promo(request):
    code = request.GET.get('code', '').strip()
    response = {'valid': False, 'discount': 0}

    try:
        promo = PromoCode.objects.get(code__iexact=code, active=True)
        response['valid'] = True
        response['discount'] = promo.discount_percent
    except PromoCode.DoesNotExist or not promo.activef:
        response['valid'] = False

    return JsonResponse(response)

# Сторінка з послугами
def services(request):
    services = Service.objects.all()
    return render(request, 'Watering/service.html', {'services': services})

# Замовлення послуги
@login_required
def order_service(request):
    if request.method == "POST":
        service_id = request.POST.get("service_id")
        service = get_object_or_404(Service, id=service_id)

        # Створення замовлення на послугу
        ServiceOrder.objects.create(
            user=request.user,
            service=service,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            email=request.user.email,
            notes=request.POST.get("notes", "")
        )

        messages.success(request, f"Ваше замовлення на '{service.title}' прийнято!")
        return redirect("services")

# Сторінка кошика
@login_required
def cart(request):
    cart_obj, created = Cart.objects.get_or_create(user=request.user)  # отримуємо або створюємо кошик для користувача

    # Фільтри
    category = request.GET.get('category')
    type_filter = request.GET.get('type')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    search = request.GET.get('search', '').strip()

    cart_items_queryset = cart_obj.items.all().select_related('item')  # отримуємо всі елементи кошика користувача

    q_filters = Q()
    if category:
        q_filters &= Q(item__category=category)

    if type_filter:
        pass 
    try:
        if price_min:
            min_price_dec = Decimal(price_min)
            q_filters &= Q(item__price__gte=min_price_dec)
        if price_max:
            max_price_dec = Decimal(price_max)
            q_filters &= Q(item__price__lte=max_price_dec)
    except Exception:
        pass

    if search:
        search_q = Q(item__name__icontains=search) | Q(item__description__icontains=search)
        q_filters &= search_q

    # застосовуємо фільтри до елементів кошика
    cart_items_filtered = cart_items_queryset.filter(q_filters)

    # Обчислення загальної ціни
    total_price = sum([item.total_price for item in cart_items_filtered])
    
    # Підготовка даних для відображення
    display_cart_items = [{
        'id': cart_item.id,
        'item': cart_item.item,
        'quantity': cart_item.quantity,
        'subtotal': cart_item.total_price, 
    } for cart_item in cart_items_filtered]  # створюємо список словників для відображення

    try:
        ItemModel = cart_items_queryset.model.item.field.related_model
    except Exception:
        ItemModel = None

    return render(request, 'Watering/cart.html', {
        'cart_items': display_cart_items,
        'total_price': total_price,
        'Item': ItemModel,
    })

# Додавання товару до кошика
@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    quantity = int(request.POST.get('quantity', 1))

    # якщо кількість некоректна, кажемо що користувач дурачок
    if quantity <= 0:
        messages.error(request, "Кількість має бути більше нуля.")
        return redirect('item_detail', item_id=item_id)

    cart, created = Cart.objects.get_or_create(user=request.user)  # отримуємо або створюємо кошик для користувача

    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)  # отримуємо або створюємо елемент кошика
    # якщо елемент вже існує, збільшуємо кількість
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f"{item.name} додано до кошика")
    return redirect('cart')

# Видалення товару з кошика
@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user) 
    cart_item.delete()
    messages.success(request, f"{cart_item.item.name} видалено з кошика")
    return redirect('cart')

# Оновлення кількості товару в кошику
@login_required
def update_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        messages.error(request, "Некоректна кількість.")
        return redirect('cart')

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Кількість {cart_item.item.name} оновлено.")
    else:
        item_name = cart_item.item.name
        cart_item.delete()
        messages.success(request, f"{item_name} видалено з кошика.")
        
    return redirect('cart')

# Очищення кошика
@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.success(request, "Кошик очищено")
    return redirect('cart')

# Оформлення замовлення для вибраних товарів у кошику
@login_required
def checkout_selected(request):
    if request.method != "POST":
        return redirect('cart')

    selected_ids_str = request.POST.get('selected_cart_items', '')  # отримуємо вибрані елементи кошика
    promo_code_input = request.POST.get('promo_code', '').strip()  # отримуємо введений промокод

    # якщо жоден елемент не вибрано, кажемо що користувач дурачок
    if not selected_ids_str:
        messages.error(request, "Не вибрано жодного товару для покупки.")
        return redirect('cart')

    # Розбиваємо рядок на список ID
    selected_ids = [int(id_str) for id_str in selected_ids_str.split(',') if id_str.isdigit()]

    # Отримуємо елементи кошика, що відповідають вибраним ID
    cart_items_queryset = CartItem.objects.filter(
        id__in=selected_ids, 
        cart__user=request.user
    ).select_related('item')

    if not cart_items_queryset:
        messages.error(request, "Вибрані товари не знайдено у вашому кошику.")
        return redirect('cart')

    promo = None
    discount = Decimal('0')

    # Перевірка промокоду
    if promo_code_input:
        try:
            promo = PromoCode.objects.get(code__iexact=promo_code_input, active=True)
            discount = Decimal(promo.discount_percent) / Decimal('100')
        except PromoCode.DoesNotExist:
            messages.warning(request, "Промокод недійсний або вже використаний.")
            promo = None
            discount = Decimal('0')

    total_raw_price = Decimal('0')
    items_to_process = []
    
    # Перевірка наявності товарів на складі
    for cart_item in cart_items_queryset:
        item = cart_item.item
        quantity = cart_item.quantity

        if quantity > item.quantity:
            messages.error(request, f"На складі доступно лише {item.quantity} шт. товару '{item.name}'. Будь ласка, зменште кількість у кошику.")
            return redirect('cart')
        
        # Збираємо дані для обробки замовлення
        items_to_process.append({
            'item': item,
            'quantity': quantity,
            'price_per_item': item.price,
            'cart_item': cart_item,
        })
        total_raw_price += item.price * quantity

    total_price_final = total_raw_price * (Decimal('1.0') - discount)

    # Створення замовлення
    order = Order.objects.create(
        user=request.user,
        total_price=total_price_final,
        promo_code=promo
    )
    # Створення елементів замовлення та оновлення кількості товарів на складі
    for data in items_to_process:
        OrderItem.objects.create(
            order=order,
            item=data['item'],
            quantity=data['quantity'],
            price_per_item=data['price_per_item']
        )
        
        item = data['item']
        item.quantity -= data['quantity']
        if item.quantity == 0:
            item.in_stock = False
        item.save()

        data['cart_item'].delete()

    if promo:
        promo.active = False
        promo.save()

    messages.success(request, f"Ваше замовлення №{order.id} успішно оформлено! Куплено {len(items_to_process)} позицій на суму {total_price_final:.2f} ₴")
    return redirect('cart')

# Інтерактивна дошка для вибору товарів
@login_required
def interactive_board(request):
    items = Item.objects.all().order_by('category', 'name') 

    context = {'items': items}
    return render(request, 'Watering/interactive_board.html', context)

# Додавання товарів з інтерактивної дошки до кошика
@login_required
def add_board_item(request):
    if request.method != 'POST':
        return redirect('interactive_board')
    board_data_json = request.POST.get('board_data')

    # якщо дані про елементи відсутні, кажемо що користувач дурачок
    if not board_data_json:
        messages.error(request, "Немає даних про елементи на полі.")
        return redirect('interactive_board')

    # Парсимо JSON-дані
    try:
        items_to_add = json.loads(board_data_json)
    except json.JSONDecodeError:
        messages.error(request, "Некоректний формат даних.")
        return redirect('interactive_board')

    # якщо жоден елемент не вибрано, кажемо що користувач дурачок
    if not items_to_add:
        messages.success(request, 'На полі не було вибрано предметів для поливу.')
        return redirect('interactive_board')
    
    cart, created = Cart.objects.get_or_create(user=request.user)  # отримуємо або створюємо кошик для користувача
    items_added_count = 0

    # Додаємо кожен вибраний елемент до кошика
    for item_data in items_to_add:
        try:
            item_id = item_data.get('id')
            quantity = float(item_data.get('quantity', 1))

            if quantity <= 0 or not item_id:
                continue

            item = get_object_or_404(Item, id=item_id)

            # Додаємо елемент до кошика
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                item=item,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            items_added_count += 1

        except Item.DoesNotExist:
            messages.warning(request, f"Товар з ID {item_id} не знайдено.")
            continue
        except ValueError:
            messages.warning(request, "Некоректна кількість товару.")
            continue
    
    # Повідомляємо користувача про результат додавання
    if items_added_count > 0:
        messages.success(request, f"Успішно додано {items_added_count} позицій з конструктора до кошика.")
        return redirect('cart')
    else:  # якщо не вдалося додати жоден товар до кошика повідомляємо про це
        messages.error(request, 'Не вдалося додати жодного дійсного товару до кошика.')
        return redirect('interactive_board')