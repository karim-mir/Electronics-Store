from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from network.admin import NetworkNodeAdmin
from network.models import Contact, NetworkNode, Product

User = get_user_model()


class AdminTests(TestCase):

    def setUp(self):
        """Настройка тестовых данных для админки"""
        self.site = AdminSite()
        self.admin = NetworkNodeAdmin(NetworkNode, self.site)
        self.factory = RequestFactory()

        # Создаем суперпользователя
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )

        # Создаем контакты
        self.factory_contact = Contact.objects.create(
            email="factory@test.com",
            country="Россия",
            city="Москва",
            street="Заводская",
            house_number="1",
        )

        self.retail_contact = Contact.objects.create(
            email="retail@test.com",
            country="Россия",
            city="Санкт-Петербург",
            street="Розничная",
            house_number="2",
        )

        # Создаем продукты
        self.product = Product.objects.create(
            name="Тестовый продукт", model="Test Model", release_date="2023-01-01"
        )

        # Создаем завод
        self.factory_node = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.factory_contact,
        )
        self.factory_node.products.add(self.product)

        # Создаем розничную сеть с задолженностью
        self.retail_network = NetworkNode.objects.create(
            name="Тестовая розничная сеть",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=self.retail_contact,
            supplier=self.factory_node,
            debt=1500.00,
        )
        self.retail_network.products.add(self.product)

    def create_request(self, user=None, method="get", data=None):
        """Создает тестовый запрос с поддержкой messages"""
        if user is None:
            user = self.superuser

        if method.lower() == "get":
            request = self.factory.get("/admin/")
        else:
            request = self.factory.post("/admin/", data or {})

        request.user = user

        # ДОБАВЛЯЕМ ПОДДЕРЖКУ MESSAGES ДЛЯ ТЕСТОВ
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        return request

    def test_clear_debt_action(self):
        """Тест admin action для очистки задолженности"""
        request = self.create_request()
        queryset = NetworkNode.objects.filter(id=self.retail_network.id)

        # Проверяем, что debt существует
        self.assertEqual(self.retail_network.debt, 1500.00)

        # Вызываем action правильно (теперь с поддержкой messages)
        self.admin.clear_debt(request, queryset)

        # Проверяем, что debt обнулился
        updated_network = NetworkNode.objects.get(id=self.retail_network.id)
        self.assertEqual(updated_network.debt, 0)

    def test_clear_debt_action_multiple_objects(self):
        """Тест очистки задолженности для нескольких объектов"""
        # Создаем еще один узел с задолженностью
        contact3 = Contact.objects.create(
            email="entrepreneur@test.com",
            country="Россия",
            city="Казань",
            street="Предпринимательская",
            house_number="3",
        )

        entrepreneur = NetworkNode.objects.create(
            name="ИП Тестовый",
            node_type=NetworkNode.NodeType.ENTREPRENEUR,
            contact=contact3,
            supplier=self.factory_node,
            debt=2500.00,
        )

        request = self.create_request()
        queryset = NetworkNode.objects.filter(
            id__in=[self.retail_network.id, entrepreneur.id]
        )

        # Вызываем action для нескольких объектов
        self.admin.clear_debt(request, queryset)

        # Проверяем, что debt обнулился у всех выбранных объектов
        updated_retail = NetworkNode.objects.get(id=self.retail_network.id)
        updated_entrepreneur = NetworkNode.objects.get(id=entrepreneur.id)

        self.assertEqual(updated_retail.debt, 0)
        self.assertEqual(updated_entrepreneur.debt, 0)
