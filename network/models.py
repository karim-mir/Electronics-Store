# network/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Contact(models.Model):
    """
    Модель для хранения контактной информации звена сети.

    Attributes:
        email (EmailField): Электронная почта
        country (CharField): Страна
        city (CharField): Город
        street (CharField): Улица
        house_number (CharField): Номер дома
    """

    email = models.EmailField(unique=True, verbose_name='Электронная почта')
    country = models.CharField(max_length=100, verbose_name='Страна')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house_number = models.CharField(max_length=10, verbose_name='Номер дома')

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return self.email


class Product(models.Model):
    """
    Модель для хранения информации о продукте.

    Attributes:
        name (CharField): Название продукта
        model (CharField): Модель продукта
        release_date (DateField): Дата выхода на рынок
    """

    name = models.CharField(max_length=100, verbose_name='Название')
    model = models.CharField(max_length=100, verbose_name='Модель')
    release_date = models.DateField(verbose_name='Дата выхода на рынок')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return f"{self.name} {self.model}"


class NetworkNode(models.Model):
    """
    Модель звена сети по продаже электроники.

    Представляет иерархическую структуру из трех уровней: завод, розничная сеть, ИП.

    Attributes:
        name (CharField): Название звена
        node_type (CharField): Тип звена (factory/retail/entrepreneur)
        contact (OneToOneField): Контактная информация
        products (ManyToManyField): Связанные продукты
        supplier (ForeignKey): Поставщик оборудования
        debt (DecimalField): Задолженность перед поставщиком
        created_at (DateTimeField): Дата создания записи
    """

    class NodeType(models.TextChoices):
        """Типы звеньев сети."""
        FACTORY = 'factory', 'Завод'
        RETAIL = 'retail', 'Розничная сеть'
        ENTREPRENEUR = 'entrepreneur', 'Индивидуальный предприниматель'

    name = models.CharField(max_length=100, verbose_name='Название')
    node_type = models.CharField(
        max_length=20,
        choices=NodeType.choices,
        verbose_name='Тип звена'
    )
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        verbose_name='Контактная информация'
    )
    products = models.ManyToManyField(
        Product,
        verbose_name='Продукты',
        blank=True
    )
    supplier = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Поставщик'
    )
    debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=0.00,
        verbose_name='Задолженность перед поставщиком'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    class Meta:
        verbose_name = 'Звено сети'
        verbose_name_plural = 'Звенья сети'
        ordering = ['-created_at']

    @property
    def hierarchy_level(self):
        """
        Вычисляет уровень иерархии звена.

        Returns:
            int: Уровень иерархии (0 для завода, 1 для РС, ссылающейся на завод, и т.д.)
        """
        if self.supplier is None:
            return 0
        return self.supplier.hierarchy_level + 1

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name}"
