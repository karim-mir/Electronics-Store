from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from network.models import Contact, Product, NetworkNode
from network.serializers import (
    ContactSerializer,
    ProductSerializer,
    NetworkNodeSerializer,
    NetworkNodeCreateUpdateSerializer
)


class SerializerTests(TestCase):

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем несколько уникальных контактов
        self.contact1 = Contact.objects.create(
            email='contact1@example.com',
            country='Россия',
            city='Москва',
            street='Тестовая 1',
            house_number='1'
        )

        self.contact2 = Contact.objects.create(
            email='contact2@example.com',
            country='Россия',
            city='Санкт-Петербург',
            street='Тестовая 2',
            house_number='2'
        )

        self.contact3 = Contact.objects.create(
            email='contact3@example.com',
            country='Россия',
            city='Казань',
            street='Тестовая 3',
            house_number='3'
        )

        self.product_data = {
            'name': 'Test Product',
            'model': 'Test Model',
            'release_date': '2023-01-01'
        }

        # Создаем объекты в базе
        self.product = Product.objects.create(**self.product_data)

        # Создаем завод с уникальным контактом
        self.factory = NetworkNode.objects.create(
            name='Test Factory',
            node_type=NetworkNode.NodeType.FACTORY,
            contact=self.contact1
        )
        self.factory.products.add(self.product)

    def test_contact_serializer_create(self):
        """Тест создания контакта через сериализатор"""
        new_contact_data = {
            'email': 'new@example.com',
            'country': 'Россия',
            'city': 'Санкт-Петербург',
            'street': 'Новая',
            'house_number': '10'
        }

        serializer = ContactSerializer(data=new_contact_data)
        self.assertTrue(serializer.is_valid())
        contact = serializer.save()
        self.assertEqual(contact.email, 'new@example.com')
        self.assertEqual(contact.city, 'Санкт-Петербург')

    def test_contact_serializer_validation(self):
        """Тест валидации контакта с неверными данными"""
        invalid_data = {
            'email': 'invalid-email',  # Неправильный email
            'country': 'Россия',
            'city': 'Москва',
            'street': 'Тестовая',
            'house_number': '1'
        }

        serializer = ContactSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_product_serializer_create(self):
        """Тест создания продукта через сериализатор"""
        new_product_data = {
            'name': 'Новый продукт',
            'model': 'Новая модель',
            'release_date': '2024-01-01'
        }

        serializer = ProductSerializer(data=new_product_data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertEqual(product.name, 'Новый продукт')
        self.assertEqual(product.model, 'Новая модель')

    def test_network_node_serializer_read(self):
        """Тест сериализатора NetworkNode для чтения"""
        serializer = NetworkNodeSerializer(self.factory)

        data = serializer.data

        # Проверяем вычисляемые поля
        self.assertEqual(data['name'], 'Test Factory')
        self.assertEqual(data['hierarchy_level'], 0)
        self.assertEqual(data['city'], 'Москва')
        self.assertEqual(data['country'], 'Россия')
        # supplier_name может отсутствовать у завода - это нормально

        # Проверяем вложенные сериализаторы
        self.assertIn('contact', data)
        self.assertIn('products', data)
        self.assertEqual(len(data['products']), 1)

    def test_network_node_create_serializer_create(self):
        """Тест создания узла через NetworkNodeCreateUpdateSerializer"""
        # Используем уникальный контакт (contact2)
        node_data = {
            'name': 'New Retail Node',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': self.contact2.id,  # Уникальный контакт
            'products': [self.product.id],
            'supplier': self.factory.id
        }

        serializer = NetworkNodeCreateUpdateSerializer(data=node_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        node = serializer.save()
        self.assertEqual(node.name, 'New Retail Node')
        self.assertEqual(node.node_type, NetworkNode.NodeType.RETAIL)
        self.assertEqual(node.supplier, self.factory)
        self.assertIn(self.product, node.products.all())

    def test_network_node_create_serializer_update(self):
        """Тест обновления узла через NetworkNodeCreateUpdateSerializer"""
        # Создаем узел для обновления с уникальным контактом
        node = NetworkNode.objects.create(
            name='Original Name',
            node_type=NetworkNode.NodeType.RETAIL,
            contact=self.contact2,  # Уникальный контакт
            supplier=self.factory
        )

        update_data = {
            'name': 'Updated Name',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': self.contact2.id,  # Тот же контакт
            'products': [self.product.id],
            'supplier': self.factory.id
        }

        serializer = NetworkNodeCreateUpdateSerializer(instance=node, data=update_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_node = serializer.save()
        self.assertEqual(updated_node.name, 'Updated Name')
        self.assertIn(self.product, updated_node.products.all())

    def test_network_node_create_serializer_validate_method(self):
        """Тест метода validate в NetworkNodeCreateUpdateSerializer"""
        serializer = NetworkNodeCreateUpdateSerializer()

        # Тестируем метод validate (строка 161)
        valid_data = {
            'name': 'Test Node',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': self.contact3.id,  # Уникальный контакт
            'products': [self.product.id],
            'supplier': self.factory.id
        }

        validated_data = serializer.validate(valid_data)
        self.assertEqual(validated_data, valid_data)

    def test_network_node_create_serializer_create_method(self):
        """Тест метода create в NetworkNodeCreateUpdateSerializer"""
        serializer = NetworkNodeCreateUpdateSerializer()

        # Используем новый уникальный контакт
        new_contact = Contact.objects.create(
            email='create_test@example.com',
            country='Россия',
            city='Екатеринбург',
            street='Создаваемая',
            house_number='100'
        )

        validated_data = {
            'name': 'Test Node',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': new_contact,
            'supplier': self.factory
        }

        # Тестируем создание с продуктами
        validated_data_with_products = {**validated_data, 'products': [self.product]}
        node = serializer.create(validated_data_with_products)

        self.assertEqual(node.name, 'Test Node')
        self.assertIn(self.product, node.products.all())

    def test_network_node_create_serializer_update_method(self):
        """Тест метода update в NetworkNodeCreateUpdateSerializer"""
        # Создаем узел для обновления с уникальным контактом
        update_contact = Contact.objects.create(
            email='update_test@example.com',
            country='Россия',
            city='Новосибирск',
            street='Обновляемая',
            house_number='200'
        )

        node = NetworkNode.objects.create(
            name='Original Name',
            node_type=NetworkNode.NodeType.RETAIL,
            contact=update_contact,
            supplier=self.factory
        )

        serializer = NetworkNodeCreateUpdateSerializer()

        # Тестируем обновление с продуктами
        validated_data = {
            'name': 'Updated Name',
            'products': [self.product]
        }

        updated_node = serializer.update(node, validated_data)

        self.assertEqual(updated_node.name, 'Updated Name')
        self.assertIn(self.product, updated_node.products.all())

    def test_network_node_create_serializer_update_without_products(self):
        """Тест метода update без изменения продуктов"""
        # Создаем узел с продуктом и уникальным контактом
        no_change_contact = Contact.objects.create(
            email='nochange_test@example.com',
            country='Россия',
            city='Владивосток',
            street='Неизменяемая',
            house_number='300'
        )

        node = NetworkNode.objects.create(
            name='Original Name',
            node_type=NetworkNode.NodeType.RETAIL,
            contact=no_change_contact,
            supplier=self.factory
        )
        node.products.add(self.product)

        serializer = NetworkNodeCreateUpdateSerializer()

        # Обновляем без изменения продуктов
        validated_data = {
            'name': 'Updated Name'
        }

        updated_node = serializer.update(node, validated_data)

        self.assertEqual(updated_node.name, 'Updated Name')
        # Продукты должны остаться неизменными
        self.assertIn(self.product, updated_node.products.all())

    def test_factory_cannot_have_supplier_validation(self):
        """Тест что завод не может иметь поставщика"""
        # Создаем новый уникальный контакт для завода
        factory_contact = Contact.objects.create(
            email='factory_test@example.com',
            country='Россия',
            city='Тюмень',
            street='Заводская',
            house_number='400'
        )

        factory_data = {
            'name': 'New Factory',
            'node_type': NetworkNode.NodeType.FACTORY,
            'contact': factory_contact.id,
            'products': [self.product.id],
            'supplier': self.factory.id  # Завод не должен иметь поставщика!
        }

        serializer = NetworkNodeCreateUpdateSerializer(data=factory_data)

        # Сериализатор должен пройти валидацию (валидация на уровне модели)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Но при сохранении модель выбросит DjangoValidationError
        # Это нормальное поведение - валидация на уровне модели
        with self.assertRaises(DjangoValidationError) as context:
            serializer.save()

        # Проверяем что ошибка содержит правильное сообщение
        self.assertIn('supplier', context.exception.error_dict)
        self.assertIn('Завод не может иметь поставщика', str(context.exception))

    def test_serializer_with_empty_products(self):
        """Тест сериализатора с пустым списком продуктов"""
        # Создаем новый уникальный контакт
        empty_products_contact = Contact.objects.create(
            email='empty_products@example.com',
            country='Россия',
            city='Сочи',
            street='Пустая',
            house_number='500'
        )

        node_data = {
            'name': 'Node Without Products',
            'node_type': NetworkNode.NodeType.RETAIL,
            'contact': empty_products_contact.id,  # Уникальный контакт
            'products': [],  # Пустой список продуктов
            'supplier': self.factory.id
        }

        serializer = NetworkNodeCreateUpdateSerializer(data=node_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        node = serializer.save()
        self.assertEqual(node.products.count(), 0)

    def test_serializer_partial_update(self):
        """Тест частичного обновления через PATCH"""
        # Создаем узел для частичного обновления
        partial_contact = Contact.objects.create(
            email='partial@example.com',
            country='Россия',
            city='Калининград',
            street='Частичная',
            house_number='600'
        )

        node = NetworkNode.objects.create(
            name='Original Name',
            node_type=NetworkNode.NodeType.RETAIL,
            contact=partial_contact,
            supplier=self.factory
        )

        # Частичное обновление только имени
        update_data = {'name': 'Partially Updated Name'}

        serializer = NetworkNodeCreateUpdateSerializer(
            instance=node,
            data=update_data,
            partial=True  # Важно для PATCH запросов
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_node = serializer.save()
        self.assertEqual(updated_node.name, 'Partially Updated Name')
        # Остальные поля должны остаться неизменными
        self.assertEqual(updated_node.node_type, NetworkNode.NodeType.RETAIL)
        self.assertEqual(updated_node.contact, partial_contact)
