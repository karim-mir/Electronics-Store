from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from network.admin import NetworkNodeAdmin
from network.models import Contact, NetworkNode, Product

User = get_user_model()


class MockRequest:
    def __init__(self, user=None):
        self.user = user


class AdminTests(TestCase):

    def setUp(self):
        """Настройка тестовых данных для админки"""
        self.site = AdminSite()
        self.admin = NetworkNodeAdmin(NetworkNode, self.site)

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
        self.factory = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.factory_contact,
        )
        self.factory.products.add(self.product)

        # Создаем розничную сеть с задолженностью
        self.retail_network = NetworkNode.objects.create(
            name="Тестовая розничная сеть",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=self.retail_contact,
            supplier=self.factory,
            debt=1500.00,
        )
        self.retail_network.products.add(self.product)

    def test_admin_supplier_link(self):
        """Тест ссылки на поставщика в админке"""
        # Для узла с поставщиком
        link = self.admin.supplier_link(self.retail_network)
        self.assertIn(str(self.factory.id), link)
        self.assertIn("href", link)
        self.assertIn("supplier", link)

        # Для узла без поставщика (завода)
        link = self.admin.supplier_link(self.factory)
        self.assertEqual(link, "-")

    def test_clear_debt_action(self):
        """Тест admin action для очистки задолженности"""
        request = MockRequest(user=self.superuser)
        queryset = NetworkNode.objects.filter(id=self.retail_network.id)

        # Проверяем, что debt существует
        self.assertEqual(self.retail_network.debt, 1500.00)

        # Вызываем action
        self.admin.clear_debt(modeladmin=None, request=request, queryset=queryset)

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
            supplier=self.factory,
            debt=2500.00,
        )

        request = MockRequest(user=self.superuser)
        queryset = NetworkNode.objects.filter(
            id__in=[self.retail_network.id, entrepreneur.id]
        )

        # Вызываем action для нескольких объектов
        self.admin.clear_debt(modeladmin=None, request=request, queryset=queryset)

        # Проверяем, что debt обнулился у всех выбранных объектов
        updated_retail = NetworkNode.objects.get(id=self.retail_network.id)
        updated_entrepreneur = NetworkNode.objects.get(id=entrepreneur.id)

        self.assertEqual(updated_retail.debt, 0)
        self.assertEqual(updated_entrepreneur.debt, 0)

    def test_city_filter(self):
        """Тест фильтра по городу в админке"""
        # Создаем узел в другом городе
        contact_other_city = Contact.objects.create(
            email="other_city@test.com",
            country="Россия",
            city="Екатеринбург",
            street="Другая",
            house_number="4",
        )

        NetworkNode.objects.create(
            name="Сеть в другом городе",
            node_type=NetworkNode.NodeType.RETAIL,
            contact=contact_other_city,
            supplier=self.factory,
        )

        # Проверяем, что фильтр по городу работает
        # Это тестирует наличие фильтра, а не его логику (которая реализована в Django)
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        filters = [str(f) for f in model_admin.get_list_filter(request=MockRequest())]

        self.assertIn("contact__city", filters)

    def test_admin_list_display(self):
        """Тест отображаемых полей в списке админки"""
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        list_display = model_admin.get_list_display(request=MockRequest())

        expected_fields = ["name", "node_type", "supplier_link", "debt", "created_at"]
        for field in expected_fields:
            self.assertIn(field, list_display)

    def test_admin_search_fields(self):
        """Тест полей поиска в админке"""
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        search_fields = model_admin.get_search_fields(request=MockRequest())

        expected_fields = ["name", "contact__email", "contact__city"]
        for field in expected_fields:
            self.assertIn(field, search_fields)

    def test_admin_list_filter(self):
        """Тест фильтров в админке"""
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        list_filter = model_admin.get_list_filter(request=MockRequest())

        expected_filters = ["node_type", "contact__city", "created_at"]
        for filter_field in expected_filters:
            self.assertIn(filter_field, list_filter)

    def test_admin_readonly_fields(self):
        """Тест readonly полей в админке"""
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        readonly_fields = model_admin.get_readonly_fields(request=MockRequest())

        self.assertIn("created_at", readonly_fields)
        self.assertIn("hierarchy_level", readonly_fields)

    def test_admin_changelist_view(self):
        """Тест отображения списка объектов в админке"""
        self.client.force_login(self.superuser)
        url = reverse("admin:network_networknode_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.factory.name)
        self.assertContains(response, self.retail_network.name)

    def test_admin_change_view(self):
        """Тест отображения формы редактирования объекта в админке"""
        self.client.force_login(self.superuser)
        url = reverse("admin:network_networknode_change", args=[self.factory.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.factory.name)
        self.assertContains(response, "supplier")  # Проверяем наличие поля поставщика

    def test_hierarchy_level_display(self):
        """Тест отображения уровня иерархии в админке"""
        hierarchy_level = self.admin.hierarchy_level(self.retail_network)
        self.assertEqual(hierarchy_level, 1)

        hierarchy_level = self.admin.hierarchy_level(self.factory)
        self.assertEqual(hierarchy_level, 0)

    def test_debt_display(self):
        """Тест форматирования отображения задолженности"""
        debt_display = self.admin.debt_display(self.retail_network)
        self.assertEqual(debt_display, "1500.00")

        # Проверяем узел без задолженности
        debt_display = self.admin.debt_display(self.factory)
        self.assertEqual(debt_display, "0.00")

    def test_admin_actions_exist(self):
        """Тест, что admin actions присутствуют"""
        model_admin = NetworkNodeAdmin(NetworkNode, self.site)
        actions = model_admin.get_actions(request=MockRequest())

        self.assertIn("clear_debt", actions)

    def test_contact_admin_representation(self):
        """Тест отображения контактов в админке"""
        # Проверяем, что контакт правильно отображается
        self.assertEqual(str(self.factory_contact), "factory@test.com (Москва, Россия)")
        self.assertEqual(
            str(self.retail_contact), "retail@test.com (Санкт-Петербург, Россия)"
        )

    def test_product_admin_representation(self):
        """Тест отображения продуктов в админке"""
        # Проверяем, что продукт правильно отображается
        self.assertEqual(str(self.product), "Тестовый продукт Test Model")
