from django.contrib import admin
from .models import Product, PriceHistory, Notification

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'platform', 'current_price', 'desired_price', 'is_active')
    list_filter = ('platform', 'is_active', 'created_at')
    search_fields = ('name', 'url', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_checked')

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'is_sent', 'created_at')
    list_filter = ('is_sent', 'created_at')
    search_fields = ('user__username', 'product__name')