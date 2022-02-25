from django.contrib import admin
from .models import TelegramGroup


@admin.register(TelegramGroup)
class Telegram(admin.ModelAdmin):
    list_display = ('name', 'active')
    search_fields = ("name",)
    list_filter = ('active',)
