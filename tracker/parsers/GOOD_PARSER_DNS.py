import pyautogui
import time
import subprocess
import pyperclip
import json
import re
import os
from datetime import datetime


def extract_product_info(raw_text):
    """Извлекает информацию о товаре из перехваченного текста"""

    product_info = {}

    # 1. Извлекаем код товара
    code_match = re.search(r'code["\s:]+"?(\d+)"?', raw_text)
    if code_match:
        product_info['code'] = code_match.group(1)

    # 2. Извлекаем название
    name_match = re.search(r'name["\s:]+"([^"]+)"', raw_text)
    if name_match:
        product_info['name'] = name_match.group(1)

    # 3. Извлекаем цену
    price_match = re.search(r'price["\s:]+(\d+)', raw_text)
    if price_match:
        product_info['price'] = int(price_match.group(1))

    # 4. Извлекаем рейтинг
    rating_match = re.search(r'rating["\s:]+([\d.]+)', raw_text)
    if rating_match:
        product_info['rating'] = float(rating_match.group(1))

    # 5. Извлекаем страну производителя
    country_match = re.search(r'manufacturerCountry["\s:]+"([^"]+)"', raw_text)
    if country_match:
        product_info['manufacturerCountry'] = country_match.group(1)

    # 6. Извлекаем гарантию
    warranty_match = re.search(r'monthWarranty["\s:]+(\d+)', raw_text)
    if warranty_match:
        product_info['monthWarranty'] = int(warranty_match.group(1))

    # 7. Извлекаем описание
    desc_match = re.search(r'description["\s:]+"([^"]+)"', raw_text)
    if desc_match:
        product_info['description'] = desc_match.group(1)

    # 8. Извлекаем изображение
    image_match = re.search(r'imageUrl["\s:]+"([^"]+)"', raw_text)
    if image_match:
        product_info['imageUrl'] = image_match.group(1)

    # 9. Извлекаем характеристики (первые 5)
    characteristics = {}

    # Ищем блок characteristics
    chars_match = re.search(r'characteristics:\s*({[^}]*?(?:{[^}]*?}[^}]*?)*})', raw_text, re.DOTALL)
    if chars_match:
        chars_text = chars_match.group(1)
        # Извлекаем основные категории
        categories = ['Общие характеристики', 'Габариты и вес', 'Датчик', 'Подключение', 'Управление']

        for category in categories:
            cat_match = re.search(f'{category}:\\s*\\[([^\\]]+)\\]', chars_text, re.DOTALL)
            if cat_match:
                cat_content = cat_match.group(1)
                specs = re.findall(r'title:\s*"([^"]+)"[^}]*value:\s*"([^"]+)"', cat_content)
                if specs:
                    characteristics[category] = [{'title': t, 'value': v} for t, v in specs[:3]]

    if characteristics:
        product_info['characteristics'] = characteristics

    # 10. Извлекаем топ-отзыв (если есть)
    opinion_match = re.search(r'topOpinion:\s*({[^}]+})', raw_text)
    if opinion_match:
        opinion_text = opinion_match.group(1)

        opinion = {}

        # Извлекаем данные отзыва
        user_match = re.search(r'userName:\s*"([^"]+)"', opinion_text)
        if user_match:
            opinion['userName'] = user_match.group(1)

        city_match = re.search(r'userCity:\s*"([^"]+)"', opinion_text)
        if city_match:
            opinion['userCity'] = city_match.group(1)

        grade_match = re.search(r'grade:\s*(\d+)', opinion_text)
        if grade_match:
            opinion['grade'] = int(grade_match.group(1))

        plus_match = re.search(r'plus:\s*"([^"]+)"', opinion_text)
        if plus_match:
            opinion['plus'] = plus_match.group(1)

        comment_match = re.search(r'comment:\s*"([^"]+)"', opinion_text)
        if comment_match:
            opinion['comment'] = comment_match.group(1)

        if opinion:
            product_info['topOpinion'] = opinion

    return product_info


def save_product_data(product_info):
    """Сохраняет информацию о товаре в файл"""

    if not product_info:
        print("❌ Нет данных для сохранения")
        return None

    # Создаем папку для данных
    os.makedirs("products_data", exist_ok=True)

    # Формируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code = product_info.get('code', 'unknown')
    filename = f"products_data/product_{code}_{timestamp}.json"

    # Сохраняем JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(product_info, f, ensure_ascii=False, indent=2)

    return filename


def print_product_info(product_info):
    """Красиво выводит информацию о товаре"""

    if not product_info:
        print("❌ Нет данных для отображения")
        return

    print("\n" + "=" * 70)
    print(f"📦 ТОВАР: {product_info.get('name', 'Неизвестно')}")
    print("=" * 70)
    print(f"📝 Код: {product_info.get('code', 'Нет')}")
    print(f"💰 Цена: {product_info.get('price', 0):,} ₽")
    print(f"⭐ Рейтинг: {product_info.get('rating', 0)}/5")
    print(f"🌍 Страна: {product_info.get('manufacturerCountry', 'Не указана')}")
    print(f"🔧 Гарантия: {product_info.get('monthWarranty', 0)} месяцев")

    if product_info.get('description'):
        desc = product_info['description'][:150]
        print(f"\n📖 Описание: {desc}...")

    # Характеристики
    if product_info.get('characteristics'):
        print("\n📊 ХАРАКТЕРИСТИКИ:")
        for category, specs in product_info['characteristics'].items():
            print(f"\n  {category}:")
            for spec in specs:
                print(f"    • {spec.get('title')}: {spec.get('value')}")

    # Отзыв
    if product_info.get('topOpinion'):
        opinion = product_info['topOpinion']
        print("\n💬 ПОПУЛЯРНЫЙ ОТЗЫВ:")
        print(f"  👤 {opinion.get('userName', 'Аноним')} ({opinion.get('userCity', '')})")
        print(f"  ⭐ Оценка: {opinion.get('grade', 0)}/5")
        if opinion.get('plus'):
            print(f"  ✅ Плюсы: {opinion.get('plus', '')[:100]}...")
        if opinion.get('comment'):
            print(f"  💬 Комментарий: {opinion.get('comment', '')[:100]}...")

    print("=" * 70)


def create_simple_report(product_info, filename):
    """Создает простой текстовый отчет"""

    report_filename = filename.replace('.json', '_report.txt')

    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write(f"ОТЧЕТ ПО ТОВАРУ\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Код товара: {product_info.get('code', 'Нет')}\n")
        f.write(f"Название: {product_info.get('name', 'Неизвестно')}\n")
        f.write(f"Цена: {product_info.get('price', 0)} ₽\n")
        f.write(f"Рейтинг: {product_info.get('rating', 0)}/5\n")
        f.write(f"Страна: {product_info.get('manufacturerCountry', 'Не указана')}\n")
        f.write(f"Гарантия: {product_info.get('monthWarranty', 0)} месяцев\n")

        if product_info.get('description'):
            f.write(f"\nОписание:\n{product_info['description']}\n")

    return report_filename


def human_capture():
    """Имитирует действия человека"""

    print("URL:")
    url = input()

    # 1. Открываем Chromium
    print("1️⃣ Открываю Chromium...")
    subprocess.Popen(['chromium', '--new-window'])

    # 2. Нажимаем Ctrl+L для фокуса на адресной строке
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(1.5)

    # 3. Вставляем URL
    pyperclip.copy(url)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)

    # 4. Нажимаем Enter
    pyautogui.press('enter')
    print("2️⃣ Страница загружается...")
    pyautogui.hotkey('f11')
    time.sleep(2)

    # 5. Открываем DevTools (F12)
    pyautogui.press('f12')
    print("3️⃣ Открываю DevTools...")
    time.sleep(2)

    """"# 6. Переходим на вкладку Network (Ctrl+[ или клик мышью)
    pyautogui.hotkey('ctrl', '[')  # Переключение вкладок в DevTools
    time.sleep(1)
    get-product=id
"""
    # 7. Обновляем страницу (Ctrl+R)
    pyautogui.hotkey('ctrl', 'r')
    print("4️⃣ Обновляю страницу...")
    time.sleep(2)

    # 9. Кликаем на найденный запрос
    pyautogui.click(x=1100, y=450)
    time.sleep(2)
    pyautogui.click(x=1210, y=300)  # Координаты нужно подобрать
    time.sleep(0.5)
    pyautogui.rightClick(x=1500, y=700)
    time.sleep(0.5)
    pyautogui.click(x=1510, y=720)
    time.sleep(0.5)
    pyautogui.click(x=1510, y=720)

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    pyautogui.rightClick(x=1510, y=600)
    time.sleep(0.5)
    pyautogui.click(x=1510, y=1000)
    time.sleep(0.3)

    # 10. Получаем скопированный текст
    raw_text = pyperclip.paste()

    # 11. ИЗВЛЕКАЕМ ДАННЫЕ ИЗ ПОЛУЧЕННОГО ТЕКСТА
    print("\n" + "=" * 50)
    print("📊 ОБРАБОТКА ДАННЫХ...")
    print("=" * 50)

    if raw_text and len(raw_text) > 100:
        # Извлекаем информацию
        product_info = extract_product_info(raw_text)

        if product_info:
            # Сохраняем в JSON
            json_file = save_product_data(product_info)

            # Создаем текстовый отчет
            report_file = create_simple_report(product_info, json_file)

            # Выводим на экран
            print_product_info(product_info)

            print(f"\n💾 Сохранено:")
            print(f"   JSON: {json_file}")
            print(f"   Отчет: {report_file}")
        else:
            print("❌ Не удалось извлечь данные из текста")
            print("\n📄 Первые 500 символов полученного текста:")
            print(raw_text[:500])
    else:
        print("❌ Не удалось скопировать данные (буфер обмена пуст)")
        print("💡 Попробуйте увеличить время ожидания или скопировать вручную")

    # 12. Закрываем браузер
    print("\n🔒 Закрываю браузер...")
    pyautogui.hotkey('alt', 'f4')


if __name__ == "__main__":
    print("ВНИМАНИЕ: Скрипт будет управлять мышью и клавиатурой!")
    print("Не трогайте мышь в течение 30 секунд\n")
    time.sleep(3)

    human_capture()