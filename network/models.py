from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Contact(models.Model):
    """
    Модель для хранения контактной информации звена сети.

    Каждое звено сети имеет уникальную контактную информацию.

    Examples:
        >>> contact = Contact.objects.create(
        ...     email="factory@example.com",
        ...     country="Россия",
        ...     city="Москва",
        ...     street="Ленина",
        ...     house_number="10"
        ... )
        >>> str(contact)
        'factory@example.com (Москва, Россия)'
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта",
        help_text="Уникальный email адрес звена сети",
    )
    country = models.CharField(
        max_length=100,
        verbose_name="Страна",
        help_text="Страна расположения звена сети",
    )
    city = models.CharField(
        max_length=100, verbose_name="Город", help_text="Город расположения звена сети"
    )
    street = models.CharField(
        max_length=100, verbose_name="Улица", help_text="Улица расположения звена сети"
    )
    house_number = models.CharField(
        max_length=10,
        verbose_name="Номер дома",
        help_text="Номер дома расположения звена сети",
    )

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        db_table = "network_contacts"

    def __str__(self):
        """Строковое представление контакта."""
        return f"{self.email} ({self.city}, {self.country})"


class Product(models.Model):
    """
    Модель для хранения информации о продукте электроники.

    Продукты могут быть связаны с несколькими звеньями сети через отношение ManyToMany.

    Attributes:
        name (CharField): Наименование продукта (например, "Смартфон")
        model (CharField): Модель продукта (например, "Galaxy S24")
        release_date (DateField): Дата выхода продукта на рынок

    Examples:
        >>> product = Product.objects.create(
        ...     name="Смартфон",
        ...     model="Galaxy S24",
        ...     release_date="2024-01-15"
        ... )
        >>> str(product)
        'Смартфон Galaxy S24'
    """

    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        help_text="Наименование продукта электроники",
    )
    model = models.CharField(
        max_length=100, verbose_name="Модель", help_text="Модель или артикул продукта"
    )
    release_date = models.DateField(
        verbose_name="Дата выхода на рынок",
        help_text="Дата первого появления продукта на рынке",
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        db_table = "network_products"
        ordering = ["name", "model"]

    def __str__(self):
        """Строковое представление продукта."""
        return f"{self.name} {self.model}"


class NetworkNode(models.Model):
    """
    Модель звена сети по продаже электроники.

    Реализует иерархическую структуру из трех уровней: завод, розничная сеть, ИП.
    Уровень иерархии вычисляется динамически на основе цепочки поставщиков.

    Attributes:
        name (CharField): Название звена сети
        node_type (CharField): Тип звена (factory/retail/entrepreneur)
        contact (OneToOneField): Контактная информация звена
        products (ManyToManyField): Продукты, доступные у звена
        supplier (ForeignKey): Поставщик оборудования (родительское звено)
        debt (DecimalField): Задолженность перед поставщиком
        created_at (DateTimeField): Дата и время создания записи

    Notes:
        - Уровень иерархии вычисляется свойством hierarchy_level
        - Завод всегда имеет уровень 0 и не может иметь поставщика
        - Запрещены циклические ссылки в цепочке поставщиков

    Examples:
        >>> # Создание завода (уровень 0)
        >>> factory = NetworkNode.objects.create(
        ...     name="Завод Электроники",
        ...     node_type=NetworkNode.NodeType.FACTORY,
        ...     contact=contact1
        ... )
        >>> factory.hierarchy_level
        0

        >>> # Создание розничной сети с поставщиком-заводом (уровень 1)
        >>> retail = NetworkNode.objects.create(
        ...     name="Розничная сеть Техно",
        ...     node_type=NetworkNode.NodeType.RETAIL,
        ...     contact=contact2,
        ...     supplier=factory
        ... )
        >>> retail.hierarchy_level
        1
    """

    class NodeType(models.TextChoices):
        """
        Допустимые типы звеньев сети.

        Attributes:
            FACTORY: Завод - производитель электроники (уровень 0)
            RETAIL: Розничная сеть - продажа через магазины (уровень 1-2)
            ENTREPRENEur: Индивидуальный предприниматель (уровень 1-2)
        """

        FACTORY = "factory", "Завод"
        RETAIL = "retail", "Розничная сеть"
        ENTREPRENEUR = "entrepreneur", "Индивидуальный предприниматель"

    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        help_text="Официальное название звена сети",
    )
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        verbose_name="Тип звена",
        help_text="Тип звена в иерархии сети",
    )
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        verbose_name="Контактная информация",
        help_text="Контактные данные звена сети",
    )
    products = models.ManyToManyField(
        Product,
        verbose_name="Продукты",
        blank=True,
        help_text="Продукты электроники, доступные у звена",
    )
    supplier = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Поставщик",
        help_text="Вышестоящее звено в цепочке поставок",
    )
    debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=0.00,
        verbose_name="Задолженность перед поставщиком",
        help_text="Денежная задолженность в рублях с точностью до копеек",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания",
        help_text="Автоматически устанавливается при создании записи",
    )

    class Meta:
        verbose_name = "Звено сети"
        verbose_name_plural = "Звенья сети"
        db_table = "network_nodes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["node_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["supplier"]),
        ]

    @property
    def hierarchy_level(self):
        """
        Вычисляет уровень иерархии звена на основе цепочки поставщиков.

        Returns:
            int: Уровень иерархии (0 для завода, 1+ для остальных звеньев)

        Raises:
            RecursionError: При обнаружении циклической ссылки (обрабатывается валидацией)

        Examples:
            >>> factory = NetworkNode(node_type=NetworkNode.NodeType.FACTORY)
            >>> factory.hierarchy_level
            0

            >>> retail = NetworkNode(node_type=NetworkNode.NodeType.RETAIL, supplier=factory)
            >>> retail.hierarchy_level
            1

            >>> entrepreneur = NetworkNode(node_type=NetworkNode.NodeType.ENTREPRENEUR, supplier=retail)
            >>> entrepreneur.hierarchy_level
            2
        """
        if self.supplier is None:
            return 0
        return self.supplier.hierarchy_level + 1

    def clean(self):
        """
        Валидация данных модели перед сохранением.

        Raises:
            ValidationError: При нарушении бизнес-правил:
                - Циклические ссылки в цепочке поставщиков
                - Самоприсваивание поставщика
                - Завод с поставщиком

        Examples:
            >>> node = NetworkNode(supplier=node)  # Самоприсваивание
            >>> node.clean()  # Raises ValidationError

            >>> factory = NetworkNode(node_type=NetworkNode.NodeType.FACTORY, supplier=retail)
            >>> factory.clean()  # Raises ValidationError - завод не может иметь поставщика
        """
        # Запрет на самоприсваивание
        if self.supplier and self.supplier.id == self.id:
            raise ValidationError(
                {"supplier": "Звено не может быть своим собственным поставщиком."}
            )

        # Проверка циклических ссылок
        if self.supplier and self.pk:
            visited = set()
            current = self.supplier

            while current and current.pk not in visited:
                if current.pk == self.pk:
                    raise ValidationError(
                        {
                            "supplier": "Обнаружена циклическая ссылка в цепочке поставщиков."
                        }
                    )
                visited.add(current.pk)
                current = current.supplier

        # Завод не должен иметь поставщика
        if self.node_type == self.NodeType.FACTORY and self.supplier:
            raise ValidationError(
                {
                    "supplier": "Завод не может иметь поставщика. Уровень завода всегда 0."
                }
            )

        # Максимальная глубина иерархии - 2 уровня
        if self.hierarchy_level > 2:
            raise ValidationError(
                {
                    "supplier": f"Превышена максимальная глубина иерархии. Текущий уровень: {self.hierarchy_level}"
                }
            )

    def save(self, *args, **kwargs):
        """
        Сохранение объекта с предварительной валидацией.

        Args:
            *args: Аргументы для родительского метода save
            **kwargs: Ключевые аргументы для родительского метода save

        Notes:
            Автоматически вызывает clean() перед сохранением для валидации данных.
        """
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Возвращает абсолютный URL для детального просмотра объекта.

        Returns:
            str: URL для доступа к детальной информации о звене сети
        """
        from django.urls import reverse

        return reverse("networknode-detail", kwargs={"pk": self.pk})

    def __str__(self):
        """Строковое представление объекта."""
        return f"{self.get_node_type_display()}: {self.name} (Уровень: {self.hierarchy_level})"
