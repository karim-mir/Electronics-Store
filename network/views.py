from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from .models import NetworkNode
from .serializers import (
    NetworkNodeListSerializer,
    NetworkNodeDetailSerializer,
    NetworkNodeCreateUpdateSerializer
)


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, позволяющее доступ только активным сотрудникам.

    Проверяет, что пользователь аутентифицирован и имеет активный статус.
    """

    def has_permission(self, request, view):
        """
        Проверяет права доступа пользователя.

        Args:
            request: HTTP запрос
            view: Представление, к которому осуществляется доступ

        Returns:
            bool: True если пользователь активен, иначе False
        """
        return request.user and request.user.is_authenticated and request.user.is_active


class NetworkNodeFilter(FilterSet):
    """
    Фильтр для звеньев сети.

    Позволяет фильтровать звенья по стране контактной информации.
    """

    country = CharFilter(field_name='contact__country', lookup_expr='iexact')

    class Meta:
        model = NetworkNode
        fields = ['contact__country']


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с звеньями сети.

    Обеспечивает:
    - Создание, чтение, обновление, удаление звеньев
    - Фильтрацию по стране
    - Автоматическое вычисление уровня иерархии
    - Запрет на обновление задолженности через API
    """

    permission_classes = [IsActiveEmployee]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NetworkNodeFilter

    def get_queryset(self):
        """
        Оптимизирует запросы к базе данных.

        Returns:
            QuerySet: Оптимизированный QuerySet с предзагрузкой связанных объектов
        """
        queryset = NetworkNode.objects.select_related(
            'contact', 'supplier'
        ).prefetch_related('products')

        # Дополнительная фильтрация по стране из query params
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(contact__country__iexact=country)

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Serializer: Соответствующий сериализатор для текущего действия
        """
        if self.action == 'list':
            return NetworkNodeListSerializer
        elif self.action == 'retrieve':
            return NetworkNodeDetailSerializer
        return NetworkNodeCreateUpdateSerializer

    def update(self, request, *args, **kwargs):
        """
        Обновляет звено сети.

        Запрещает обновление поля 'debt' через API.

        Args:
            request: HTTP запрос
            *args: Дополнительные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: Ответ с обновленными данными
        """
        # Запрещаем обновление поля debt через API
        if 'debt' in request.data:
            request.data.pop('debt')
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def hierarchy_stats(self, request):
        """
        Пользовательское действие для получения статистики по иерархии.

        Returns:
            Response: Статистика по количеству звеньев каждого уровня
        """
        stats = {}
        for node_type, _ in NetworkNode.NodeType.choices:
            stats[node_type] = {
                'total': NetworkNode.objects.filter(node_type=node_type).count(),
                'by_level': {}
            }

            # Группируем по уровням иерархии
            nodes = NetworkNode.objects.filter(node_type=node_type)
            for node in nodes:
                level = node.hierarchy_level
                if level not in stats[node_type]['by_level']:
                    stats[node_type]['by_level'][level] = 0
                stats[node_type]['by_level'][level] += 1

        return Response(stats)
