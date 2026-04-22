#!/usr/bin/env python
# manual_parser.py

import time
import sys
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import django
import traceback
import json
import re
from asgiref.sync import sync_to_async

# Настройка Django
sys.path.append('/home/artem/work/price_tracker')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tracker.models import Product
from django.utils import timezone


@sync_to_async
def get_product(product_id):
    """Получение товара из БД (синхронно)"""
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None


@sync_to_async
def save_product(product):
    """Сохранение товара в БД (синхронно)"""
    product.save()


@sync_to_async
def create_price_history(product, price):
    """Создание записи истории цен (синхронно)"""
    from tracker.models import PriceHistory
    PriceHistory.objects.create(
        product=product,
        price=price
    )


async def extract_price_from_text(text):
    """Извлекает все возможные цены из текста"""
    prices = []
    if text:
        # Ищем числа, которые могут быть ценами (от 100 до 100000)
        numbers = re.findall(r'(\d+[\.,]?\d*)', text.replace(' ', ''))
        for num in numbers:
            try:
                val = float(num.replace(',', '.'))
                # Отсекаем слишком маленькие и слишком большие числа
                if 100 < val < 100000:
                    prices.append(val)
                elif 1000000 < val < 10000000:  # Если в копейках
                    prices.append(val / 100)
            except:
                continue
    return prices


async def is_valid_product_page(page):
    """Проверяет, что загружена нормальная страница товара, а не заглушка"""
    title = await page.title()
    content = await page.content()
    content_lower = content.lower()

    # Проверяем признаки нормальной страницы
    has_h1 = await page.query_selector('h1') is not None
    has_price = await page.query_selector('span[itemprop="price"], span[class*="price"]') is not None

    # Проверяем признаки заглушки
    is_error = any(word in title.lower() for word in ['ошибка', 'error', 'доступ', 'ограничен'])
    is_captcha = any(word in content_lower for word in ['captcha', 'robot', 'проверка'])

    if is_error and not has_h1 and not has_price:
        print(f"⚠️ Обнаружена страница-заглушка: {title}")
        return False

    return True


async def wait_for_valid_page(page, timeout=30):
    """Ждет, пока не загрузится валидная страница"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if await is_valid_product_page(page):
            return True
        print("⏳ Страница еще не загрузилась, ждем...")
        await asyncio.sleep(2)
    return False


async def parse_with_headless(product, page):
    """Парсинг в headless режиме с выбором наиболее вероятной цены"""
    print("📑 Получаем данные...")

    # Ждем нормальной загрузки страницы
    if not await wait_for_valid_page(page):
        print("❌ Не удалось загрузить валидную страницу товара")
        return False

    title = await page.title()
    print(f"📑 Заголовок: {title}")

    # Парсим название - ищем h1
    name_elem = await page.query_selector('h1')
    if name_elem:
        product_name = await name_elem.text_content()
        product_name = product_name.strip() if product_name else title.split('—')[0].strip()
    else:
        product_name = title.split('—')[0].strip()
    print(f"📝 Название: {product_name}")

    # Собираем все возможные цены
    all_prices = []

    # 1. Ищем в JSON-LD (самый надежный источник)
    print("🔍 Ищем цены в JSON-LD...")
    json_ld = await page.query_selector('script[type="application/ld+json"]')
    if json_ld:
        try:
            json_text = await json_ld.text_content()
            data = json.loads(json_text)

            if data.get('offers'):
                offers = data['offers']
                if isinstance(offers, dict):
                    price = offers.get('price', 0)
                    if price:
                        price_val = float(price)
                        all_prices.append(price_val)
                        print(f"   📌 Найдена цена в offers: {price_val}")
                elif isinstance(offers, list):
                    for offer in offers:
                        if offer.get('price'):
                            price_val = float(offer['price'])
                            all_prices.append(price_val)
                            print(f"   📌 Найдена цена в offers: {price_val}")
        except Exception as e:
            print(f"   ⚠️ Ошибка парсинга JSON-LD: {e}")

    # 2. Ищем цену в специфичных для Ozon селекторах (основная цена)
    print("🔍 Ищем основную цену товара...")
    main_price_selectors = [
        'div[data-widget="webPrice"] span[class*="c3015-a1"]',
        'div[data-widget="webPrice"] span[class*="tsHeadline500Medium"]',
        'span[data-widget="webPrice"] span[class*="c3015-a1"]',
        'span[itemprop="price"]',
        'div[class*="price"] span[class*="c3015"]',
    ]

    for selector in main_price_selectors:
        elements = await page.query_selector_all(selector)
        for elem in elements:
            text = await elem.text_content()
            if text:
                import re
                numbers = re.findall(r'(\d+[\.,]?\d*)', text.replace(' ', ''))
                for num in numbers:
                    try:
                        price_val = float(num.replace(',', '.'))
                        if 500 < price_val < 20000:  # Реалистичный диапазон для одежды
                            all_prices.append(price_val)
                            print(f"   📌 Основная цена {price_val} в селекторе {selector}")
                    except:
                        continue

    # 3. Ищем все остальные цены (для статистики)
    print("🔍 Ищем дополнительные цены...")
    other_selectors = [
        'span[class*="price"]',
        'div[class*="price"] span',
        'span[class*="tsHeadline500Medium"]',
    ]

    for selector in other_selectors:
        if selector not in main_price_selectors:  # Избегаем дублирования
            elements = await page.query_selector_all(selector)
            for elem in elements:
                text = await elem.text_content()
                prices = await extract_price_from_text(text)
                if prices:
                    all_prices.extend(prices)

    # Анализируем найденные цены
    if all_prices:
        # Фильтруем цены в реалистичном диапазоне
        realistic_prices = [p for p in all_prices if 500 < p < 20000]

        print(f"\n📊 Всего найдено цен: {len(all_prices)}")
        print(f"📊 Реалистичных цен (500-20000): {len(realistic_prices)}")

        if realistic_prices:
            # Находим наиболее часто встречающуюся цену
            from collections import Counter
            price_counts = Counter(realistic_prices)
            most_common_price = price_counts.most_common(1)[0]

            print(f"\n📊 Распределение цен:")
            for price, count in price_counts.most_common(5):
                print(f"   Цена {price} встречается {count} раз")

            price = most_common_price[0]
            print(f"\n💰 ИТОГОВАЯ ЦЕНА: {price} ₽ (наиболее частая в реалистичном диапазоне)")
        else:
            # Если нет реалистичных цен, используем JSON-LD или медиану
            if 500 < max(all_prices) < 20000:
                price = max(all_prices)
                print(f"\n💰 ИТОГОВАЯ ЦЕНА: {price} ₽ (максимальная из найденных)")
            else:
                # Сортируем и берем цену из середины (медиану)
                sorted_prices = sorted(all_prices)
                median_idx = len(sorted_prices) // 2
                price = sorted_prices[median_idx]
                print(f"\n💰 ИТОГОВАЯ ЦЕНА: {price} ₽ (медианная)")
    else:
        price = None
        print("⚠️ Цена не найдена")

    # Парсим изображение
    print("🔍 Ищем изображение товара...")
    img_selectors = [
        'meta[property="og:image"]',
        'img[itemprop="image"]',
        'div[data-widget="webGallery"] img',
        'img[class*="gallery"]',
        'img[src*="cdn"]'
    ]

    image_url = None
    for selector in img_selectors:
        if selector.startswith('meta'):
            img = await page.query_selector(selector)
            if img:
                image_url = await img.get_attribute('content')
        else:
            imgs = await page.query_selector_all(selector)
            for img in imgs:
                src = await img.get_attribute('src')
                if src and ('cdn' in src or 'multimedia' in src):
                    image_url = src
                    print(f"🖼️ Найдено изображение товара")
                    break
        if image_url:
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            break

    # Сохраняем в базу
    old_price = product.current_price

    product.name = product_name[:500]
    product.current_price = price
    product.image_url = image_url
    product.last_checked = timezone.now()

    await save_product(product)
    print(f"✅ Товар сохранен в БД")

    if price and (old_price != price):
        await create_price_history(product, price)
        print(f"📊 История цен обновлена (было {old_price}, стало {price})")

    print(f"\n✅ Данные сохранены в базу!")
    print(f"   Название: {product_name}")
    print(f"   Цена: {price} ₽" if price else "   Цена не найдена")
    print(f"   Изображение: {image_url[:100]}..." if image_url else "   Изображение не найдено")

    return True


async def manual_parse(product_id):
    """Ручной парсинг товара с открытием браузера на сервере"""
    print("\n" + "=" * 60)
    print(f"🔍 РУЧНОЙ ПАРСИНГ ТОВАРА #{product_id}")
    print("=" * 60)

    # Получаем товар из БД
    product = await get_product(product_id)
    if not product:
        print(f"❌ Товар с ID {product_id} не найден")
        return

    print(f"📦 Название: {product.name or 'Без названия'}")
    print(f"🔗 URL: {product.url}")
    print("=" * 60 + "\n")

    browser = None
    try:
        async with async_playwright() as p:
            # Сначала пробуем headless режим
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1280, 'height': 1024},
                locale='ru-RU',
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            print("🌐 Загружаю страницу...")
            await page.goto(product.url, timeout=60000)

            print("✅ Страница загружена")

            # Проверяем наличие капчи
            page_content = await page.content()
            page_content_lower = page_content.lower()

            captcha_keywords = ['captcha', 'robot', 'проверка', 'подтвердите', 'turnstile', 'recaptcha']
            has_captcha = any(keyword in page_content_lower for keyword in captcha_keywords)

            if has_captcha:
                print("🚫 Обнаружена капча!")
                print("📢 Закрываю headless браузер и открываю GUI для решения...")

                # Закрываем headless браузер
                await browser.close()

                # Запускаем браузер с GUI
                print("🔄 Открываю браузер с GUI...")
                gui_browser = await p.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                gui_context = await gui_browser.new_context(
                    viewport={'width': 1280, 'height': 1024},
                    locale='ru-RU'
                )
                gui_page = await gui_context.new_page()

                print("🌐 Загружаю страницу в видимом браузере...")
                await gui_page.goto(product.url, timeout=60000)

                input("\n🔄 Решите капчу в открытом окне браузера, затем нажмите Enter...")

                # Проверяем, что загрузилась правильная страница
                if not await wait_for_valid_page(gui_page):
                    print("⚠️ Страница товара не загрузилась. Возможно, нужно обновить страницу вручную.")
                    input("\n🔄 Обновите страницу в браузере и нажмите Enter...")

                # Парсим данные после решения капчи
                await parse_with_headless(product, gui_page)

                input("\n✅ Нажмите Enter для закрытия браузера...")
                await gui_browser.close()

                return

            # Если капчи нет, парсим в headless режиме
            await parse_with_headless(product, page)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        traceback.print_exc()
    finally:
        if browser:
            print("\n🔄 Закрываю браузер...")
            await browser.close()


def main():
    if len(sys.argv) != 2:
        print("Использование: python manual_parser.py <product_id>")
        sys.exit(1)

    try:
        product_id = int(sys.argv[1])
        asyncio.run(manual_parse(product_id))
    except ValueError:
        print("❌ Неверный ID товара")
        sys.exit(1)


if __name__ == "__main__":
    main()