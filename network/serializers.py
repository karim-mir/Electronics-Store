from rest_framework import serializers
from .models import Contact, Product, NetworkNode


class ContactSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Contact."""

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Product."""

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id']


class NetworkNodeListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка звеньев сети.

    Оптимизирован для отображения в списке - содержит только основные поля.
    """

    contact = ContactSerializer(read_only=True)
    hierarchy_level = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    city = serializers.CharField(source='contact.city', read_only=True)
    country = serializers.CharField(source='contact.country', read_only=True)

    class Meta:
        model = NetworkNode
        fields = [
            'id', 'name', 'node_type', 'hierarchy_level', 'city', 'country',
            'supplier_name', 'debt', 'created_at'
        ]


class NetworkNodeDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального просмотра звена сети.

    Содержит полную информацию о звене, включая связанные объекты.
    """

    contact = ContactSerializer()
    products = ProductSerializer(many=True, read_only=True)
    hierarchy_level = serializers.ReadOnlyField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = NetworkNode
        fields = '__all__'
        read_only_fields = ['debt', 'created_at', 'hierarchy_level']


class NetworkNodeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления звеньев сети.

    Запрещает обновление поля 'debt' через API.
    """

    class Meta:
        model = NetworkNode
        fields = ['id', 'name', 'node_type', 'contact', 'products', 'supplier']
        read_only_fields = ['debt']

    def validate_supplier(self, value):
        """
        Валидация поставщика.

        Args:
            value: Объект NetworkNode, который устанавливается как поставщик

        Returns:
            NetworkNode: Проверенный объект поставщика

        Raises:
            serializers.ValidationError: Если поставщик невалиден
        """
        if value and value == self.instance:
            raise serializers.ValidationError("Звено не может быть своим собственным поставщиком.")
        return value
