from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from django.db.models import Count, Sum
from .models import NetworkNode
from .serializers import NetworkNodeSerializer, NetworkNodeCreateUpdateSerializer


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, предоставляющее доступ только активным сотрудникам.

    Проверяет, что пользователь аутентифицирован и имеет статус is_active=True.

    Methods:
        has_permission: Основная проверка прав доступа

    Examples:
        >>> permission = IsActiveEmployee()
        >>> request.user.is_authenticated = True
        >>> request.user.is_active = True
        >>> permission.has_permission(request, view)
        True
    """

    def has_permission(self, request, view):
        """
        Проверяет права доступа пользователя к API.

        Args:
            request (Request): Объект HTTP запроса
            view (APIView): Объект представления, к которому осуществляется доступ

        Returns:
            bool: True если пользователь активен и аутентифицирован, иначе False

        Notes:
            - Возвращает False для анонимных пользователей
            - Возвращает False для неактивных пользователей
            - Возвращает True для активных аутентифицированных пользователей
        """
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class NetworkNodeFilter(FilterSet):
    """
    Фильтр для NetworkNode с поддержкой фильтрации по стране.

    Позволяет фильтровать звенья сети по стране контактной информации.

    Attributes:
        country (CharFilter): Фильтр по точному совпадению страны (case-insensitive)

    Examples:
        >>> /api/v1/network-nodes/?country=Россия
        >>> /api/v1/network-nodes/?country=США
    """

    country = CharFilter(
        field_name='contact__country',
        lookup_expr='iexact',
        help_text='Фильтрация по стране (регистронезависимая)'
    )

    class Meta:
        model = NetworkNode
        fields = ['contact__country']


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для выполнения CRUD операций с моделью NetworkNode.

    Обеспечивает полный набор операций:
    - CREATE (POST): Создание нового звена сети
    - READ (GET): Получение списка или детальной информации
    - UPDATE (PUT/PATCH): Обновление существующего звена
    - DELETE (DELETE): Удаление звена сети

    Attributes:
        permission_classes: Разрешения доступа
        filter_backends: Бэкенды фильтрации
        filterset_class: Класс фильтров
        queryset: Базовый QuerySet

    Examples:
        >>> # Получение списка всех звеньев
        >>> response = client.get('/api/v1/network-nodes/')

        >>> # Фильтрация по стране
        >>> response = client.get('/api/v1/network-nodes/?country=Россия')

        >>> # Создание нового звена
        >>> response = client.post('/api/v1/network-nodes/', {
        ...     'name': 'Новая сеть',
        ...     'node_type': 'retail',
        ...     ...
        ... })
    """

    permission_classes = [IsActiveEmployee]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NetworkNodeFilter

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet для NetworkNode.

        Returns:
            QuerySet: QuerySet с предзагрузкой связанных объектов и фильтрацией

        Notes:
            - Использует select_related для контактов и поставщиков
            - Использует prefetch_related для продуктов
            - Поддерживает фильтрацию по стране через query parameters

        Examples:
            >>> queryset = NetworkNodeViewSet().get_queryset()
            >>> queryset.query  # SQL запрос с JOINs
        """
        queryset = NetworkNode.objects.select_related(
            'contact', 'supplier'
        ).prefetch_related('products')

        # Дополнительная фильтрация по стране из query parameters
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(contact__country__iexact=country)

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от выполняемого действия.

        Returns:
            Serializer: Класс сериализатора для текущего действия

        Notes:
            - Для create/update/partial_update использует NetworkNodeCreateUpdateSerializer
            - Для остальных действий использует NetworkNodeSerializer

        Examples:
            >>> view = NetworkNodeViewSet()
            >>> view.action = 'list'
            >>> view.get_serializer_class()
            <class 'NetworkNodeSerializer'>
        """
        if self.action in ['create', 'update', 'partial_update']:
            return NetworkNodeCreateUpdateSerializer
        return NetworkNodeSerializer

    def update(self, request, *args, **kwargs):
        """
        Обрабатывает запросы на обновление объекта.

        Args:
            request (Request): HTTP запрос
            *args: Дополнительные позиционные аргументы
            **kwargs: Дополнительные именованные аргументы

        Returns:
            Response: HTTP ответ с результатом операции

        Raises:
            PermissionDenied: При попытке обновления поля 'debt'

        Examples:
            >>> # Разрешено: обновление названия
            >>> client.patch('/api/v1/network-nodes/1/', {'name': 'Новое название'})

            >>> # Запрещено: обновление задолженности
            >>> client.patch('/api/v1/network-nodes/1/', {'debt': '1000.00'})
            HTTP 403 Forbidden
        """
        # Запрет обновления задолженности через API
        if 'debt' in request.data:
            return Response(
                {
                    'error': 'Обновление задолженности запрещено через API',
                    'detail': 'Используйте админ-панель для изменения задолженности'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Пользовательское действие для получения статистики по сети.

        Returns:
            Response: Статистика по количеству звеньев, задолженностям и т.д.

        Examples:
            >>> GET /api/v1/network-nodes/statistics/
            {
                'total_nodes': 150,
                'nodes_by_type': {'factory': 10, 'retail': 100, 'entrepreneur': 40},
                'total_debt': 500000.00,
                ...
            }
        """
        stats = {
            'total_nodes': NetworkNode.objects.count(),
            'nodes_by_type': dict(NetworkNode.objects
                                  .values_list('node_type')
                                  .annotate(count=Count('id'))),
            'total_debt': NetworkNode.objects.aggregate(
                total=Sum('debt')
            )['total'] or 0,
            'countries_count': NetworkNode.objects
            .values_list('contact__country', flat=True)
            .distinct().count(),
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def clear_debt(self, request, pk=None):
        """
        Очищает задолженность для конкретного звена сети.

        Args:
            request (Request): HTTP запрос
            pk (int): Primary key объекта

        Returns:
            Response: Результат операции

        Examples:
            >>> POST /api/v1/network-nodes/1/clear_debt/
            {'message': 'Задолженность очищена', 'new_debt': 0.00}
        """
        node = self.get_object()
        old_debt = node.debt
        node.debt = 0
        node.save()

        return Response({
            'message': 'Задолженность успешно очищена',
            'old_debt': float(old_debt),
            'new_debt': 0.00,
            'node': node.name
        })
