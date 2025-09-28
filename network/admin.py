from django.contrib import admin
from django.utils.html import format_html
from .models import Contact, Product, NetworkNode


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Админ-панель для модели Contact."""

    list_display = ['email', 'country', 'city', 'street', 'house_number']
    list_filter = ['country', 'city']
    search_fields = ['email', 'country', 'city']
    list_per_page = 20


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админ-панель для модели Product."""

    list_display = ['name', 'model', 'release_date']
    list_filter = ['release_date']
    search_fields = ['name', 'model']
    list_per_page = 20


@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    """Админ-панель для модели NetworkNode."""

    list_display = ['name', 'node_type', 'hierarchy_level', 'supplier_link',
                    'city_filter', 'debt', 'created_at']
    list_filter = ['node_type', 'contact__city', 'contact__country', 'created_at']
    search_fields = ['name', 'contact__email', 'contact__city']
    list_per_page = 20
    readonly_fields = ['hierarchy_level', 'created_at']
    actions = ['clear_debt']

    def supplier_link(self, obj):
        """
        Отображает ссылку на поставщика в админ-панели.

        Args:
            obj: Объект NetworkNode

        Returns:
            str: HTML ссылка на поставщика или текст "Нет поставщика"
        """
        if obj.supplier:
            return format_html(
                '<a href="{}">{}</a>',
                f'/admin/network/networknode/{obj.supplier.id}/change/',
                obj.supplier.name
            )
        return "Нет поставщика"

    supplier_link.short_description = 'Поставщик'
    supplier_link.admin_order_field = 'supplier'

    def city_filter(self, obj):
        """
        Отображает город для фильтрации в админ-панели.

        Args:
            obj: Объект NetworkNode

        Returns:
            str: Название города из контактной информации
        """
        return obj.contact.city

    city_filter.short_description = 'Город'
    city_filter.admin_order_field = 'contact__city'

    def clear_debt(self, request, queryset):
        """
        Admin action для очистки задолженности у выбранных объектов.

        Args:
            request: HTTP запрос
            queryset: Выбранные объекты для обработки
        """
        updated = queryset.update(debt=0)
        self.message_user(
            request,
            f'Задолженность очищена для {updated} объектов'
        )

    clear_debt.short_description = 'Очистить задолженность перед поставщиком'

    def get_queryset(self, request):
        """
        Оптимизирует запросы к базе данных.

        Args:
            request: HTTP запрос

        Returns:
            QuerySet: Оптимизированный QuerySet
        """
        return super().get_queryset(request).select_related('contact', 'supplier')
