from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Contact(models.Model):
    """
    Модель контактной информации для звена сети.

    Attributes:
        email (EmailField): Электронная почта (уникальная)
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
        db_table = 'network_contacts'

    def __str__(self):
        return f"{self.email} ({self.city}, {self.country})"


class Product(models.Model):
    """
    Модель продукта, который продается в сети.

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
        db_table = 'network_products'
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.name} {self.model}"


class NetworkNode(models.Model):
    """
    Модель звена сети по продаже электроники.

    Иерархическая структура: Завод -> Розничная сеть -> Индивидуальный предприниматель
    Каждое звено ссылается на одного поставщика оборудования.

    Attributes:
        name (CharField): Название звена
        node_type (CharField): Тип звена (factory/retail/entrepreneur)
        contact (OneToOneField): Контактная информация
        products (ManyToManyField): Продукты, которые продает звено
        supplier (ForeignKey): Поставщик оборудования (может быть любого уровня)
        debt (DecimalField): Задолженность перед поставщиком
        created_at (DateTimeField): Время создания записи
    """

    class NodeType(models.TextChoices):
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
        related_name='network_nodes'
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
        db_table = 'network_nodes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['node_type']),
            models.Index(fields=['created_at']),
        ]

    @property
    def hierarchy_level(self) -> int:
        """
        Вычисляет уровень иерархии звена.

        Returns:
            int: Уровень иерархии (0 для завода без поставщика)

        Examples:
            >>> Завод без поставщика: уровень 0
            >>> Розничная сеть, ссылающаяся на завод: уровень 1
            >>> ИП, ссылающийся на розничную сеть: уровень 2
        """
        if self.supplier is None:
            return 0
        return self.supplier.hierarchy_level + 1

    def clean(self):
        """Валидация модели перед сохранением."""
        from django.core.exceptions import ValidationError

        # Запрещаем циклические ссылки
        if self.supplier and self.supplier == self:
            raise ValidationError({'supplier': 'Звено не может быть своим собственным поставщиком.'})

        # Проверяем, что поставщик не является потомком
        if self.supplier and self.pk:
            current = self.supplier
            while current:
                if current == self:
                    raise ValidationError({'supplier': 'Обнаружена циклическая ссылка в цепочке поставщиков.'})
                current = current.supplier

    def save(self, *args, **kwargs):
        """Переопределяем save для добавления валидации."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name} (Уровень: {self.hierarchy_level})"
