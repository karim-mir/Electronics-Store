from django.db.models import Count, Sum
from django_filters import CharFilter, FilterSet
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import NetworkNode
from .serializers import (NetworkNodeCreateUpdateSerializer,
                          NetworkNodeSerializer)


class IsActiveEmployee(permissions.BasePermission):
    """
    Разрешение, предоставляющее доступ только активным сотрудникам.
    """

    def has_permission(self, request, view):
        # Сначала проверяем аутентификацию
        if not request.user or not request.user.is_authenticated:
            return False
        # Затем проверяем, что пользователь активен
        return request.user.is_active


class NetworkNodeFilter(FilterSet):
    """
    Фильтр для NetworkNode с поддержкой фильтрации по стране.
    """

    country = CharFilter(
        field_name="contact__country",
        lookup_expr="iexact",
        help_text="Фильтрация по стране (регистронезависимая)",
    )

    class Meta:
        model = NetworkNode
        fields = ["country"]


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для выполнения CRUD операций с моделью NetworkNode.
    """

    queryset = NetworkNode.objects.all()
    serializer_class = NetworkNodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]  # Убрали DjangoFilterBackend
    search_fields = ["name", "contact__city", "contact__country"]

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet для NetworkNode.
        """
        queryset = NetworkNode.objects.select_related(
            "contact", "supplier"
        ).prefetch_related("products")

        # Ручная фильтрация по стране
        country = self.request.query_params.get("country")
        if country:
            queryset = queryset.filter(contact__country__iexact=country)

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от выполняемого действия.
        """
        if self.action in ["create", "update", "partial_update"]:
            return NetworkNodeCreateUpdateSerializer
        return NetworkNodeSerializer

    def update(self, request, *args, **kwargs):
        """
        Обрабатывает запросы на обновление объекта.
        """
        if "debt" in request.data:
            return Response(
                {
                    "error": "Обновление задолженности запрещено через API",
                    "detail": "Используйте админ-панель для изменения задолженности",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Обрабатывает запросы на частичное обновление объекта.
        """
        if "debt" in request.data:
            return Response(
                {
                    "error": "Обновление задолженности запрещено через API",
                    "detail": "Используйте админ-панель для изменения задолженности",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Пользовательское действие для получения статистики по сети.
        """
        stats = {
            "total_nodes": NetworkNode.objects.count(),
            "total_debt": NetworkNode.objects.aggregate(total=Sum("debt"))["total"]
            or 0,
            "countries_count": NetworkNode.objects.values("contact__country")
            .distinct()
            .count(),
            "nodes_by_type": dict(
                NetworkNode.objects.values_list("node_type").annotate(count=Count("id"))
            ),
        }
        return Response(stats)

    @action(detail=True, methods=["post"])
    def clear_debt(self, request, pk=None):
        """
        Очищает задолженность для конкретного звена сети.
        """
        node = self.get_object()
        old_debt = node.debt
        node.debt = 0
        node.save()

        return Response(
            {
                "message": "Задолженность успешно очищена",
                "old_debt": float(old_debt),
                "new_debt": 0.00,
                "node": node.name,
            }
        )
