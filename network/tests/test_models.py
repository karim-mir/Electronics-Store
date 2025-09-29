from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from network.models import Contact, NetworkNode, Product


class ModelTests(TestCase):

    def setUp(self):
        """Настройка тестовых данных"""
        self.contact = Contact.objects.create(
            email="test@example.com",
            country="Россия",
            city="Москва",
            street="Тестовая",
            house_number="1",
        )

        self.product = Product.objects.create(
            name="Тестовый продукт",
            model="Test Model",
            release_date=timezone.now().date(),
        )

        self.factory = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.contact,
        )
        self.factory.products.add(self.product)

    def test_factory_creation(self):
        """Тест создания завода"""
        self.assertEqual(self.factory.name, "Тестовый завод")
        self.assertEqual(self.factory.node_type, NetworkNode.NodeType.FACTORY)
        self.assertEqual(self.factory.hierarchy_level, 0)
        self.assertIsNone(self.factory.supplier)
        self.assertEqual(self.factory.debt, 0)
        self.assertIsNotNone(self.factory.created_at)

    def test_retail_network_creation(self):
        """Тест создания розничной сети"""
        contact = Contact.objects.create(
            email="retail@test.com",
            country="Россия",
            city="Санкт-Петербург",
            street="Невский",
            house_number="25",
        )

        retail_network = NetworkNode.objects.create(
            name="Тестовая сеть",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=contact,
            supplier=self.factory,
            debt=1000.50,
        )
        retail_network.products.add(self.product)

        self.assertEqual(retail_network.name, "Тестовая сеть")
        self.assertEqual(retail_network.node_type, NetworkNode.NodeType.RETAIL)
        self.assertEqual(retail_network.supplier, self.factory)
        self.assertEqual(retail_network.hierarchy_level, 1)
        self.assertEqual(retail_network.debt, 1000.50)

    def test_entrepreneur_creation(self):
        """Тест создания ИП"""
        contact = Contact.objects.create(
            email="ip@test.com",
            country="Россия",
            city="Казань",
            street="Баумана",
            house_number="10",
        )

        entrepreneur = NetworkNode.objects.create(
            name="ИП Иванов",
            node_type=NetworkNode.NodeType.ENTREPRENEUR,
            contact=contact,
            supplier=self.factory,
            debt=500.75,
        )
        entrepreneur.products.add(self.product)

        self.assertEqual(entrepreneur.name, "ИП Иванов")
        self.assertEqual(entrepreneur.node_type, NetworkNode.NodeType.ENTREPRENEUR)
        self.assertEqual(entrepreneur.supplier, self.factory)
        self.assertEqual(entrepreneur.hierarchy_level, 1)
        self.assertEqual(entrepreneur.debt, 500.75)

    def test_hierarchy_level_calculation(self):
        """Тест вычисления уровня иерархии"""
        # Завод - уровень 0
        self.assertEqual(self.factory.hierarchy_level, 0)

        # Розничная сеть от завода - уровень 1
        retail_contact = Contact.objects.create(
            email="retail@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="1",
        )
        retail = NetworkNode.objects.create(
            name="Розничная сеть",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=retail_contact,
            supplier=self.factory,
        )
        self.assertEqual(retail.hierarchy_level, 1)

        # ИП от розничной сети - уровень 2
        ip_contact = Contact.objects.create(
            email="ip@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="2",
        )
        entrepreneur = NetworkNode.objects.create(
            name="ИП Тест",
            node_type=NetworkNode.NodeType.ENTREPRENEUR,
            contact=ip_contact,
            supplier=retail,
        )
        self.assertEqual(entrepreneur.hierarchy_level, 2)

    def test_factory_cannot_have_supplier(self):
        """Тест, что завод не может иметь поставщика"""
        contact = Contact.objects.create(
            email="factory2@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="1",
        )

        factory = NetworkNode(
            name="Новый завод",
            node_type=NetworkNode.NodeType.FACTORY,
            contact=contact,
            supplier=self.factory,  # Завод не может иметь поставщика!
        )

        with self.assertRaises(ValidationError):
            factory.full_clean()

    def test_circular_reference_validation(self):
        """Тест валидации циклических ссылок"""
        contact1 = Contact.objects.create(
            email="node1@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="1",
        )

        contact2 = Contact.objects.create(
            email="node2@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="2",
        )

        node1 = NetworkNode.objects.create(
            name="Узел 1",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=contact1,
            supplier=self.factory,
        )

        node2 = NetworkNode.objects.create(
            name="Узел 2",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=contact2,
            supplier=node1,
        )

        # Пытаемся создать циклическую ссылку
        node1.supplier = node2

        with self.assertRaises(ValidationError):
            node1.full_clean()

    def test_self_supplier_validation(self):
        """Тест, что узел не может быть своим поставщиком"""
        contact = Contact.objects.create(
            email="self@test.com",
            country="Россия",
            city="Город",
            street="Улица",
            house_number="1",
        )

        node = NetworkNode(
            name="Самопоставщик",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=contact,
            supplier=None,
        )
        node.save()  # Сначала сохраняем без поставщика

        # Пытаемся установить самого себя как поставщика
        node.supplier = node

        with self.assertRaises(ValidationError):
            node.full_clean()

    def test_str_methods(self):
        """Тест строкового представления объектов"""
        self.assertEqual(str(self.factory), "Завод: Тестовый завод (Уровень: 0)")
        self.assertEqual(str(self.product), "Тестовый продукт Test Model")
        self.assertEqual(str(self.contact), "test@example.com (Москва, Россия)")
