# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, PriceHistory, Notification
from .forms import CustomUserCreationForm, ProductForm
import json
import logging
import subprocess
import os

logger = logging.getLogger(__name__)


def index(request):
    """Главная страница"""
    return render(request, 'tracker/index.html')


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '🎉 Регистрация прошла успешно!')
            return redirect('profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    """Профиль пользователя со списком товаров"""
    products = request.user.products.all()
    notifications = request.user.notifications.filter(is_sent=False)[:10]
    return render(request, 'tracker/profile.html', {
        'products': products,
        'notifications': notifications
    })


@login_required
def add_product(request):
    """Добавление нового товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()

            messages.success(request, '✅ Товар успешно добавлен!')
            return redirect('profile')
    else:
        form = ProductForm()

    return render(request, 'tracker/add_product.html', {'form': form})


# tracker/views.py (должны быть все эти функции)

@login_required
def product_detail(request, product_id):
    """Детальная страница товара с графиком цен"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
    price_history = product.price_history.all()[:50]

    dates = [h.created_at.strftime('%d.%m %H:%M') for h in price_history]
    prices = [float(h.price) for h in price_history]

    context = {
        'product': product,
        'price_history': price_history,
        'dates_json': json.dumps(dates[::-1]),
        'prices_json': json.dumps(prices[::-1]),
    }
    return render(request, 'tracker/product_detail.html', context)


@login_required
def delete_product(request, product_id):
    """Удаление товара"""
    product = get_object_or_404(Product, id=product_id, user=request.user)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'🗑️ Товар "{product_name}" успешно удален')
    else:
        messages.error(request, '❌ Неверный метод запроса')

    return redirect('profile')


@login_required
def manual_parse(request, product_id):
    """Запуск ручного парсинга на сервере"""
    product = get_object_or_404(Product, id=product_id, user=request.user)

    # Путь к скрипту
    script_path = os.path.join(os.path.dirname(__file__), '..', 'manual_parser.py')

    if not os.path.exists(script_path):
        messages.error(request, '❌ Скрипт парсинга не найден')
        return redirect('profile')

    try:
        # Запускаем в фоне
        subprocess.Popen(['python', script_path, str(product.id)])
        messages.success(request, f'🖥️ Запущен ручной парсинг товара "{product.name}". Смотрите терминал сервера.')
    except Exception as e:
        messages.error(request, f'❌ Ошибка запуска: {e}')

    return redirect('profile')