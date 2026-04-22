# tracker/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Product, PriceHistory, Notification
import logging

logger = logging.getLogger(__name__)


@shared_task
def parse_product_price(product_id):
    """
    Заглушка - парсинг теперь происходит в отдельном скрипте
    """
    logger.info(f"📝 Задача на парсинг товара {product_id} создана")
    return f"Запущен ручной парсинг товара {product_id}"


@shared_task
def create_notification(product_id, price):
    """
    Создание уведомления о достижении цены
    """
    try:
        product = Product.objects.get(id=product_id)

        # Проверяем, не отправляли ли уже уведомление сегодня
        recent_notification = Notification.objects.filter(
            product=product,
            is_sent=True,
            created_at__date=timezone.now().date()
        ).exists()

        if recent_notification:
            logger.info(f"⏭️ Уведомление уже отправлено сегодня")
            return f"Уведомление уже отправлено"

        message = f"🎉 Товар '{product.name}' достиг желаемой цены! Текущая цена: {price}₽"

        notification = Notification.objects.create(
            user=product.user,
            product=product,
            message=message
        )
        logger.info(f"📬 Уведомление создано")

        # Отправляем email
        send_notification_email.delay(notification.id)

        return f"Уведомление создано"
    except Exception as e:
        logger.error(f"Ошибка создания уведомления: {e}")
        return f"Ошибка: {e}"


@shared_task
def send_notification_email(notification_id):
    """
    Отправка email уведомления
    """
    try:
        notification = Notification.objects.get(id=notification_id, is_sent=False)

        subject = f"💰 Цена достигла желаемого уровня! - {notification.product.name}"
        message = f"""
        Здравствуйте, {notification.user.username}!

        {notification.message}

        Товар: {notification.product.name}
        Текущая цена: {notification.product.current_price}₽
        Желаемая цена: {notification.product.desired_price}₽
        Ссылка на товар: {notification.product.url}

        --
        Price Tracker
        """

        # Для разработки - вывод в консоль
        logger.info(f"📧 Email для {notification.user.email}:")
        logger.info(f"Тема: {subject}")
        logger.info(f"Сообщение: {message}")

        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()

        return f"Email готов к отправке"
    except Exception as e:
        logger.error(f"Ошибка отправки email: {e}")
        return f"Ошибка: {e}"