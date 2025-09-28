from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from network.models import NetworkNode, Contact, Product

User = get_user_model()


class APITests(APITestCase):

    def setUp(self):
        """Настройка тестовых данных для API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )

        # Создаем контакты для России
        self.contact_ru1 = Contact.objects.create(
            email='contact_ru1@test.com',
            country='Россия',
            city='Москва',
            street='Улица 1',
            house_number='1'
        )

        self.contact_ru2 = Contact.objects.create(
            email='contact_ru2@test.com',
            country='Россия',
            city='Санкт-Петербург',
            street='Улица 2',
            house_number='2'
        )

        # Создаем контакт для USA
        self.contact_usa = Contact.objects.create(
            email='contact_usa@test.com',
            country='USA',
            city='New York',
            street='Street 1',
            house_number='100'
        )

        # Создаем контакт для Germany
        self.contact_germany = Contact.objects.create(
            email='contact_germany@test.com',
            country='Germany',
            city='Berlin',
            street='Strasse 1',
            house_number='50'
        )

        self.product = Product.objects.create(
            name='Test Product',
            model='Test Model',
            release_date='2023-01-01'
        )

        # Создаем узлы в России
        self.factory_ru = NetworkNode.objects.create(
            name='Factory RU',
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.contact_ru1
        )
        self.factory_ru.products.add(self.product)

        self.retail_ru = NetworkNode.objects.create(
            name='Retail RU',
            node_type=NetworkNode.NodeType.RETAIL,
            contact=self.contact_ru2,
            supplier=self.factory_ru,
            debt=1000.00
        )
        self.retail_ru.products.add(self.product)

        # Создаем узел в USA
        self.factory_usa = NetworkNode.objects.create(
            name='Factory USA',
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.contact_usa
        )
        self.factory_usa.products.add(self.product)

        # Создаем узел в Germany
        self.factory_germany = NetworkNode.objects.create(
            name='Factory Germany',
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.contact_germany
        )
        self.factory_germany.products.add(self.product)

    def get_api_url(self):
        """Получить правильный базовый URL API"""
        return '/api/v1/network-nodes/'

    def test_authentication_required(self):
        """Тест, что API требует аутентификации"""
        response = self.client.get(self.get_api_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_network_node_list_api(self):
        """Тест получения списка узлов сети"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_api_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должно быть 4 узла
        self.assertEqual(len(response.data), 4)

    def test_country_filter_russia(self):
        """Тест фильтрации по России"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"{self.get_api_url()}?country=Россия")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Должны вернуться только 2 узла из России
        self.assertEqual(len(response.data), 2)

        # Проверяем, что все возвращенные узлы из России
        for node in response.data:
            self.assertEqual(node['country'], 'Россия')

    def test_country_filter_usa(self):
        """Тест фильтрации по USA"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"{self.get_api_url()}?country=USA")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Должен вернуться 1 узел из USA
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['country'], 'USA')

    def test_country_filter_germany(self):
        """Тест фильтрации по Germany"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"{self.get_api_url()}?country=Germany")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Должен вернуться 1 узел из Germany
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['country'], 'Germany')

    def test_filter_by_nonexistent_country(self):
        """Тест фильтрации по несуществующей стране"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"{self.get_api_url()}?country=France")  # Страна, которой нет в данных
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должен вернуться пустой список
        self.assertEqual(len(response.data), 0)

    def test_network_node_create_api(self):
        """Тест создания узла сети через API"""
        self.client.force_authenticate(user=self.user)

        # Создаем новый контакт
        new_contact = Contact.objects.create(
            email='new_contact@test.com',
            country='Россия',
            city='Новосибирск',
            street='Новая',
            house_number='15'
        )

        data = {
            'name': 'New Retail Network',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': new_contact.id,
            'supplier': self.factory_ru.id,
            'products': [self.product.id]
        }

        response = self.client.post(self.get_api_url(), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Retail Network')

    def test_debt_field_read_only_on_update(self):
        """Тест, что поле debt нельзя обновить через PATCH"""
        self.client.force_authenticate(user=self.user)

        # Пытаемся обновить debt через PATCH
        data = {'debt': 0}
        url = f"{self.get_api_url()}{self.retail_ru.id}/"
        response = self.client.patch(url, data)

        # Должен вернуться запрет
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_clear_debt_action(self):
        """Тест действия очистки задолженности"""
        self.client.force_authenticate(user=self.user)

        url = f"{self.get_api_url()}{self.retail_ru.id}/clear_debt/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_debt'], 0.00)

        # Проверяем, что debt обнулился в базе
        updated_node = NetworkNode.objects.get(id=self.retail_ru.id)
        self.assertEqual(updated_node.debt, 0)

    def test_statistics_action(self):
        """Тест действия получения статистики"""
        self.client.force_authenticate(user=self.user)

        url = f"{self.get_api_url()}statistics/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_nodes', response.data)
        self.assertIn('total_debt', response.data)
        self.assertEqual(response.data['total_nodes'], 4)
