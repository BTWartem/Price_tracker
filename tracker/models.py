from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Product(models.Model):
    PLATFORM_CHOICES = [
        ('wb', 'Wildberries'),
        ('ozon', 'Ozon'),
        ('ali', 'AliExpress'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    url = models.URLField(max_length=500)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    name = models.CharField(max_length=500)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    desired_price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.current_price}₽"

    def save(self, *args, **kwargs):
        if not self.platform:
            if 'wildberries' in self.url or 'wb.ru' in self.url:
                self.platform = 'wb'
            elif 'ozon' in self.url:
                self.platform = 'ozon'
            elif 'aliexpress' in self.url:
                self.platform = 'ali'
        super().save(*args, **kwargs)


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Price histories'

    def __str__(self):
        return f"{self.product.name} - {self.price}₽ ({self.created_at})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username} - {self.product.name}"