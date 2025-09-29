from django.contrib import admin
from django.utils.html import format_html

from .models import Contact, NetworkNode, Product


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админ-класс для модели Contact."""

    list_display = ["email", "country", "city", "street", "house_number"]
    list_filter = ["country", "city"]
    search_fields = ["email", "country", "city"]
    list_per_page = 20


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админ-класс для модели Product."""

    list_display = ["name", "model", "release_date"]
    list_filter = ["release_date"]
    search_fields = ["name", "model"]
    list_per_page = 20


@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    """Админ-класс для модели NetworkNode."""

    list_display = [
        "name",
        "node_type",
        "hierarchy_level",
        "supplier_link",
        "city_filter",
        "debt",
        "created_at",
    ]
    list_filter = ["node_type", "contact__city", "contact__country", "created_at"]
    search_fields = ["name", "contact__email", "contact__city"]
    list_per_page = 20
    readonly_fields = ["hierarchy_level", "created_at"]
    actions = ["clear_debt"]

    def supplier_link(self, obj):
        """
        Отображает ссылку на поставщика в списке объектов.

        Args:
            obj: Экземпляр NetworkNode

        Returns:
            str: HTML-ссылка на поставщика или текст "Нет поставщика"
        """
        if obj.supplier:
            return format_html(
                '<a href="{}">{}</a>',
                f"/admin/network/networknode/{obj.supplier.id}/change/",
                obj.supplier.name,
            )
        return "Нет поставщика"

    supplier_link.short_description = "Поставщик"

    def city_filter(self, obj):
        """
        Отображает город для фильтрации в админке.

        Args:
            obj: Экземпляр NetworkNode

        Returns:
            str: Название города
        """
        return obj.contact.city

    city_filter.short_description = "Город"

    def clear_debt(self, request, queryset):
        """
        Admin action для очистки задолженности у выбранных объектов.

        Args:
            request: Объект запроса
            queryset: Выбранные объекты
        """
        updated_count = queryset.update(debt=0)
        self.message_user(
            request, f"Задолженность очищена для {updated_count} объектов"
        )

    clear_debt.short_description = "Очистить задолженность перед поставщиком"
