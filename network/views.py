from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from .models import NetworkNode
from .serializers import NetworkNodeSerializer, NetworkNodeCreateSerializer


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, предоставляющее доступ только активным сотрудникам.

    Проверяет, что пользователь аутентифицирован и имеет статус is_active=True.
    """

    def has_permission(self, request, view):
        """
        Проверяет права доступа пользователя.

        Args:
            request: Объект запроса
            view: Объект представления

        Returns:
            bool: True если доступ разрешен, иначе False
        """
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class NetworkNodeFilter(FilterSet):
    """
    Фильтр для NetworkNode.

    Позволяет фильтровать звенья сети по стране.
    """

    country = CharFilter(field_name='contact__country', lookup_expr='iexact')

    class Meta:
        model = NetworkNode
        fields = ['contact__country']


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для выполнения CRUD операций с NetworkNode.

    Обеспечивает:
    - Создание, чтение, обновление и удаление звеньев сети
    - Фильтрацию по стране
    - Автоматическое вычисление уровня иерархии
    - Запрет на обновление задолженности через API
    """

    permission_classes = [IsActiveEmployee]
    filter_backends = [DjangoFilterBackend]
    filterset_class = NetworkNodeFilter

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet для NetworkNode.

        Returns:
            QuerySet: QuerySet с предзагрузкой связанных объектов
        """
        queryset = NetworkNode.objects.all()
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(contact__country__iexact=country)
        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        Returns:
            Serializer: Класс сериализатора для текущего действия
        """
        if self.action == 'create':
            return NetworkNodeCreateSerializer
        return NetworkNodeSerializer

    def perform_update(self, serializer):
        """
        Выполняет обновление объекта.

        Запрещает обновление поля 'debt' через API.

        Args:
            serializer: Экземпляр сериализатора
        """
        if 'debt' in serializer.validated_data:
            del serializer.validated_data['debt']
        serializer.save()
