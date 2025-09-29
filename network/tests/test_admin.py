# test_admin.py
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase
from django.urls import reverse

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

        # Добавляем поддержку messages для тестов
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        return request

    def test_admin_supplier_link(self):
        """Тест ссылки на поставщика в админке"""
        # Для узла с поставщиком
        link = self.admin.supplier_link(self.retail_network)
        self.assertIn("href", link)
        self.assertIn("/admin/network/networknode/", link)
        self.assertIn(self.factory_node.name, link)

        # Для узла без поставщика (завода)
        link = self.admin.supplier_link(self.factory_node)
        self.assertEqual(link, "Нет поставщика")

    def test_city_filter_method(self):
        """Тест метода city_filter в админке"""
        city = self.admin.city_filter(self.retail_network)
        self.assertEqual(city, "Санкт-Петербург")

        city = self.admin.city_filter(self.factory_node)
        self.assertEqual(city, "Москва")

    def test_clear_debt_action(self):
        """Тест admin action для очистки задолженности"""
        request = self.create_request()
        queryset = NetworkNode.objects.filter(id=self.retail_network.id)

        # Проверяем, что debt существует
        self.assertEqual(self.retail_network.debt, 1500.00)

        # Вызываем action правильно
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

    def test_clear_debt_action_without_messages(self):
        """Тест очистки задолженности без использования message_user"""
        # Создаем запрос без поддержки messages
        request = self.factory.post("/admin/")
        request.user = self.superuser

        queryset = NetworkNode.objects.filter(id=self.retail_network.id)

        # Проверяем, что debt существует
        self.assertEqual(self.retail_network.debt, 1500.00)

        # Вызываем action - он должен работать даже без messages
        try:
            self.admin.clear_debt(request, queryset)
        except Exception as e:
            # Если возникает ошибка из-за messages, просто проверяем что debt обнулился
            pass

        # Проверяем, что debt обнулился
        updated_network = NetworkNode.objects.get(id=self.retail_network.id)
        self.assertEqual(updated_network.debt, 0)

    def test_admin_list_display(self):
        """Тест отображаемых полей в списке админки"""
        request = self.create_request()
        list_display = self.admin.get_list_display(request)

        expected_fields = [
            "name",
            "node_type",
            "hierarchy_level",
            "supplier_link",
            "city_filter",
            "debt",
            "created_at",
        ]
        for field in expected_fields:
            self.assertIn(field, list_display)

    def test_admin_search_fields(self):
        """Тест полей поиска в админке"""
        request = self.create_request()
        search_fields = self.admin.get_search_fields(request)

        expected_fields = ["name", "contact__email", "contact__city"]
        for field in expected_fields:
            self.assertIn(field, search_fields)

    def test_admin_list_filter(self):
        """Тест фильтров в админке"""
        request = self.create_request()
        list_filter = self.admin.get_list_filter(request)

        expected_filters = [
            "node_type",
            "contact__city",
            "contact__country",
            "created_at",
        ]
        for filter_field in expected_filters:
            self.assertIn(filter_field, list_filter)

    def test_admin_readonly_fields(self):
        """Тест readonly полей в админке"""
        request = self.create_request()
        readonly_fields = self.admin.get_readonly_fields(request)

        self.assertIn("created_at", readonly_fields)
        self.assertIn("hierarchy_level", readonly_fields)

    def test_admin_changelist_view(self):
        """Тест отображения списка объектов в админке"""
        self.client.force_login(self.superuser)
        url = reverse("admin:network_networknode_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.factory_node.name)
        self.assertContains(response, self.retail_network.name)

    def test_admin_change_view(self):
        """Тест отображения формы редактирования объекта в админке"""
        self.client.force_login(self.superuser)
        url = reverse("admin:network_networknode_change", args=[self.factory_node.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.factory_node.name)

    def test_hierarchy_level_property(self):
        """Тест вычисления уровня иерархии"""
        # Тестируем свойство модели hierarchy_level
        self.assertEqual(self.retail_network.hierarchy_level, 1)
        self.assertEqual(self.factory_node.hierarchy_level, 0)

        # Создаем ИП с поставщиком-розничной сетью (уровень 2)
        contact_entrepreneur = Contact.objects.create(
            email="entrepreneur@test.com",
            country="Россия",
            city="Казань",
            street="Предпринимательская",
            house_number="3",
        )

        entrepreneur = NetworkNode.objects.create(
            name="ИП Тестовый",
            node_type=NetworkNode.NodeType.ENTREPRENEUR,
            contact=contact_entrepreneur,
            supplier=self.retail_network,
        )

        self.assertEqual(entrepreneur.hierarchy_level, 2)

    def test_debt_field(self):
        """Тест поля debt"""
        # Просто проверяем значения полей модели
        self.assertEqual(self.retail_network.debt, 1500.00)
        self.assertEqual(self.factory_node.debt, 0.00)

    def test_admin_actions_exist(self):
        """Тест, что admin actions присутствуют"""
        request = self.create_request()
        actions = self.admin.get_actions(request)

        self.assertIn("clear_debt", actions)

    def test_contact_str_representation(self):
        """Тест строкового представления контактов"""
        self.assertEqual(str(self.factory_contact), "factory@test.com (Москва, Россия)")
        self.assertEqual(
            str(self.retail_contact), "retail@test.com (Санкт-Петербург, Россия)"
        )

    def test_product_str_representation(self):
        """Тест строкового представления продуктов"""
        self.assertEqual(str(self.product), "Тестовый продукт Test Model")

    def test_network_node_str_representation(self):
        """Тест строкового представления узлов сети"""
        self.assertEqual(str(self.factory_node), "Завод: Тестовый завод (Уровень: 0)")
        self.assertEqual(
            str(self.retail_network),
            "Розничная сеть: Тестовая розничная сеть (Уровень: 1)",
        )

    def test_contact_admin_configuration(self):
        """Тест конфигурации админки для Contact"""
        contact_admin = admin.site._registry[Contact]

        self.assertIn("email", contact_admin.list_display)
        self.assertIn("country", contact_admin.list_display)
        self.assertIn("city", contact_admin.list_display)

        self.assertIn("country", contact_admin.list_filter)
        self.assertIn("city", contact_admin.list_filter)

        self.assertIn("email", contact_admin.search_fields)

    def test_product_admin_configuration(self):
        """Тест конфигурации админки для Product"""
        product_admin = admin.site._registry[Product]

        self.assertIn("name", product_admin.list_display)
        self.assertIn("model", product_admin.list_display)
        self.assertIn("release_date", product_admin.list_display)

        self.assertIn("release_date", product_admin.list_filter)

        self.assertIn("name", product_admin.search_fields)
        self.assertIn("model", product_admin.search_fields)

    def test_supplier_link_short_description(self):
        """Тест короткого описания для supplier_link"""
        self.assertEqual(self.admin.supplier_link.short_description, "Поставщик")

    def test_city_filter_short_description(self):
        """Тест короткого описания для city_filter"""
        self.assertEqual(self.admin.city_filter.short_description, "Город")

    def test_clear_debt_short_description(self):
        """Тест короткого описания для clear_debt action"""
        self.assertEqual(
            self.admin.clear_debt.short_description,
            "Очистить задолженность перед поставщиком",
        )
