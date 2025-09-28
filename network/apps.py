# network/apps.py
from django.apps import AppConfig


class NetworkConfig(AppConfig):
    """Конфигурация приложения network."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network'
    verbose_name = 'Сетевая структура'
