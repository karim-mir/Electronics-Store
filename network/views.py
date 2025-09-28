from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from django.db.models import Count, Sum
from .models import NetworkNode
from .serializers import NetworkNodeSerializer, NetworkNodeCreateUpdateSerializer


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, предоставляющее доступ только активным сотрудникам.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class NetworkNodeFilter(FilterSet):
    """
    Фильтр для NetworkNode с поддержкой фильтрации по стране.
    """
    country = CharFilter(
        field_name='country',  # Исправлено: было 'contact__country'
        lookup_expr='iexact',
        help_text='Фильтрация по стране (регистронезависимая)'
    )

    class Meta:
        model = NetworkNode
        fields = ['country']  # Исправлено: было ['contact__country']


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для выполнения CRUD операций с моделью NetworkNode.
    """
    queryset = NetworkNode.objects.all()
    serializer_class = NetworkNodeSerializer
    permission_classes = [IsAuthenticated]  # Или [IsActiveEmployee] если хотите использовать ваш кастомный
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # Теперь filters определен
    filterset_class = NetworkNodeFilter  # Используем кастомный фильтр
    search_fields = ['name', 'city']

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet для NetworkNode.
        """
        queryset = NetworkNode.objects.all()

        # Дополнительная фильтрация по стране из query parameters
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__iexact=country)  # Исправлено: было contact__country

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от выполняемого действия.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return NetworkNodeCreateUpdateSerializer
        return NetworkNodeSerializer

    def update(self, request, *args, **kwargs):
        """
        Обрабатывает запросы на обновление объекта.
        """
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
        """
        stats = {
            'total_nodes': NetworkNode.objects.count(),
            'total_debt': NetworkNode.objects.aggregate(
                total=Sum('debt')
            )['total'] or 0,
            'countries_count': NetworkNode.objects.values('country').distinct().count(),
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def clear_debt(self, request, pk=None):
        """
        Очищает задолженность для конкретного звена сети.
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
