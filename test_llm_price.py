#!/usr/bin/env python
# test_llm_price.py

import requests
import json


def test_model_on_price():
    """Тестирует модель на задаче извлечения цены"""

    # Тестовый HTML фрагмент с ценой (имитация страницы Ozon)
    test_html = """
    <div class="product-card">
        <h1>Кроссовки BAASPLOA натуральная кожа</h1>
        <div class="price-block">
            <span class="old-price">5 731 ₽</span>
            <span class="current-price">4 452 ₽</span>
            <span class="discount">-22%</span>
        </div>
        <div class="rating">4.8</div>
    </div>
    """

    prompt = f"""Ты - AI ассистент для парсинга цен на Ozon.
Извлеки из HTML кода:
1. Название товара
2. Текущую цену (со скидкой)
3. Оригинальную цену (без скидки)

Верни ТОЛЬКО JSON в формате:
{{"name": "...", "current_price": 4452, "original_price": 5731}}

HTML:
{test_html}

JSON:"""

    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "qwen2.5:7b",  # или "llama3.2:3b"
        "prompt": prompt,
        "stream": False,
        "temperature": 0.1,
        "max_tokens": 200
    })

    if response.status_code == 200:
        result = response.json()
        print("🤖 Ответ модели:")
        print(result.get('response', ''))
    else:
        print(f"❌ Ошибка: {response.status_code}")


if __name__ == "__main__":
    test_model_on_price()