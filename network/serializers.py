from rest_framework import serializers
from .models import Contact, Product, NetworkNode


class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Contact.

    Используется для преобразования объектов Contact в JSON и обратно.

    Attributes:
        Meta.model: Модель Contact
        Meta.fields: Все поля модели
        Meta.read_only_fields: Поля только для чтения

    Examples:
        >>> serializer = ContactSerializer(data={
        ...     'email': 'test@example.com',
        ...     'country': 'Россия',
        ...     'city': 'Москва',
        ...     'street': 'Тверская',
        ...     'house_number': '15'
        ... })
        >>> serializer.is_valid()
        True
        >>> contact = serializer.save()
    """

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Product.

    Обеспечивает сериализацию/десериализацию данных о продуктах.

    Examples:
        >>> serializer = ProductSerializer(data={
        ...     'name': 'Ноутбук',
        ...     'model': 'ThinkPad X1',
        ...     'release_date': '2024-03-01'
        ... })
        >>> serializer.is_valid()
        True
        >>> product = serializer.save()
    """

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id']


class NetworkNodeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения данных NetworkNode.

    Включает вычисляемые поля и вложенные сериализаторы для связанных объектов.
    Используется для операций чтения (GET).

    Attributes:
        contact (ContactSerializer): Вложенный сериализатор контактов
        products (ProductSerializer): Вложенный сериализатор продуктов
        hierarchy_level (ReadOnlyField): Вычисляемый уровень иерархии
        supplier_name (CharField): Название поставщика
        city (CharField): Город из контактной информации
        country (CharField): Страна из контактной информации

    Examples:
        >>> node = NetworkNode.objects.get(pk=1)
        >>> serializer = NetworkNodeSerializer(node)
        >>> serializer.data
        {
            'id': 1,
            'name': 'Завод Электроники',
            'node_type': 'factory',
            'hierarchy_level': 0,
            'city': 'Москва',
            'country': 'Россия',
            ...
        }
    """

    contact = ContactSerializer(read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    hierarchy_level = serializers.ReadOnlyField(
        help_text='Уровень иерархии, вычисляемый на основе цепочки поставщиков'
    )
    supplier_name = serializers.CharField(
        source='supplier.name',
        read_only=True,
        help_text='Название поставщика оборудования'
    )
    city = serializers.CharField(
        source='contact.city',
        read_only=True,
        help_text='Город расположения звена сети'
    )
    country = serializers.CharField(
        source='contact.country',
        read_only=True,
        help_text='Страна расположения звена сети'
    )

    class Meta:
        model = NetworkNode
        fields = '__all__'
        read_only_fields = ['debt']


class NetworkNodeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления NetworkNode.

    Используется для операций создания (POST) и обновления (PUT/PATCH).
    Запрещает прямое обновление поля 'debt' через API.

    Notes:
        - Поле 'debt' доступно только для чтения
        - Валидация бизнес-правил выполняется на уровне модели

    Examples:
        >>> serializer = NetworkNodeCreateUpdateSerializer(data={
        ...     'name': 'Новая сеть',
        ...     'node_type': 'retail',
        ...     'contact': 1,
        ...     'products': [1, 2],
        ...     'supplier': 3
        ... })
        >>> serializer.is_valid()
        True
    """

    class Meta:
        model = NetworkNode
        fields = ['id', 'name', 'node_type', 'contact', 'products', 'supplier']
        read_only_fields = ['debt']

    def validate(self, data):
        """
        Дополнительная валидация данных при создании/обновлении.

        Args:
            data (dict): Данные для валидации

        Returns:
            dict: Проверенные и очищенные данные

        Raises:
            serializers.ValidationError: При нарушении бизнес-правил

        Examples:
            >>> # Проверка, что завод не имеет поставщика
            >>> if data.get('node_type') == 'factory' and data.get('supplier'):
            ...     raise ValidationError({'supplier': 'Завод не может иметь поставщика'})
        """
        # Дополнительная бизнес-логика валидации может быть добавлена здесь
        return data

    def create(self, validated_data):
        """
        Создание нового объекта NetworkNode.

        Args:
            validated_data (dict): Проверенные данные для создания

        Returns:
            NetworkNode: Созданный объект

        Notes:
            Автоматически обрабатывает ManyToMany поле products
        """
        products_data = validated_data.pop('products', [])
        node = NetworkNode.objects.create(**validated_data)
        node.products.set(products_data)
        return node

    def update(self, instance, validated_data):
        """
        Обновление существующего объекта NetworkNode.

        Args:
            instance (NetworkNode): Обновляемый объект
            validated_data (dict): Проверенные данные для обновления

        Returns:
            NetworkNode: Обновленный объект
        """
        products_data = validated_data.pop('products', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if products_data is not None:
            instance.products.set(products_data)

        return instance
