# Price Tracker

Сервис для отслеживания цен на товары с DNS-Shop и других маркетплейсов.

## Функции

- Автоматический парсинг цен
- История изменения цен
- Email уведомления о снижении цены
- Регистрация и личный кабинет

## Технологии

- Python 3.11
- Django
- PostgreSQL
- Celery
- Redis

## Установка

Клонирование репозитория:

git clone git@github.com:BTWartem/Price_tracker.git
cd Price_tracker

Создание виртуального окружения:

python -m venv .venv
source .venv/bin/activate

Установка зависимостей:

pip install -r requirements.txt
