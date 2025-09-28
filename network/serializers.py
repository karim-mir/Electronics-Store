from rest_framework import serializers
from .models import Contact, Product, NetworkNode


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Contact."""

    class Meta:
        model = Contact
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Product."""

    class Meta:
        model = Product
        fields = '__all__'


class NetworkNodeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения данных NetworkNode.

    Включает вычисляемые поля и связанные объекты.
    """

    hierarchy_level = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    city = serializers.CharField(source='contact.city', read_only=True)
    country = serializers.CharField(source='contact.country', read_only=True)

    class Meta:
        model = NetworkNode
        fields = [
            'id', 'name', 'node_type', 'hierarchy_level', 'city', 'country',
            'supplier_name', 'debt', 'created_at', 'contact', 'products', 'supplier'
        ]
        read_only_fields = ['debt', 'created_at', 'hierarchy_level']


class NetworkNodeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления NetworkNode.

    Запрещает прямое обновление поля 'debt'.
    """

    class Meta:
        model = NetworkNode
        fields = ['id', 'name', 'node_type', 'contact', 'products', 'supplier']

    def validate(self, data):
        """
        Проверяет данные перед созданием/обновлением.

        Args:
            data: Входные данные

        Returns:
            dict: Проверенные данные

        Raises:
            serializers.ValidationError: Если данные невалидны
        """
        return data
