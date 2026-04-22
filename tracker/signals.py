from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


@receiver(post_migrate)
def setup_periodic_tasks(sender, **kwargs):
    if sender.name == 'tracker':
        # Создаем интервал в 6 часов
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=6,
            period=IntervalSchedule.HOURS,
        )

        # Задача обновления всех цен
        PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Update all prices every 6 hours',
            task='tracker.tasks.update_all_prices',
        )

        # Создаем интервал в 24 часа для очистки
        daily_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=24,
            period=IntervalSchedule.HOURS,
        )

        # Задача очистки старой истории
        PeriodicTask.objects.get_or_create(
            interval=daily_schedule,
            name='Cleanup old price history daily',
            task='tracker.tasks.cleanup_old_price_history',
        )

        # Создаем интервал в 1 час для повторных попыток
        hourly_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )

        # Задача повторных попыток
        PeriodicTask.objects.get_or_create(
            interval=hourly_schedule,
            name='Retry failed parsing hourly',
            task='tracker.tasks.retry_failed_parsing',
        )