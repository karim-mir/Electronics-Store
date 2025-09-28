from django.core.management.base import BaseCommand
from faker import Faker

from network.models import Contact, NetworkNode, Product


class Command(BaseCommand):
    help = "Seed database with test data for electronics store network"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        fake = Faker("ru_RU")

        if options["clear"]:
            self.clear_data()

        self.stdout.write("Seeding database...")

        # Создаем продукты
        products = self.create_products(fake)

        # Создаем контакты
        contacts = self.create_contacts(fake)

        # Создаем узлы сети
        network_nodes = self.create_network_nodes(fake, contacts, products)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded database: "
                f"{len(products)} products, "
                f"{len(contacts)} contacts, "
                f"{len(network_nodes)} network nodes"
            )
        )

    def clear_data(self):
        """Очистка существующих данных"""
        self.stdout.write("Clearing existing data...")
        NetworkNode.objects.all().delete()
        Contact.objects.all().delete()
        Product.objects.all().delete()

    def create_products(self, fake):
        """Создание тестовых продуктов"""
        products_data = [
            {
                "name": "Смартфон",
                "model": "Galaxy S23",
                "release_date": fake.date_between(start_date="-2y", end_date="today"),
            },
            {
                "name": "Ноутбук",
                "model": "ThinkPad X1",
                "release_date": fake.date_between(start_date="-1y", end_date="today"),
            },
            {
                "name": "Планшет",
                "model": "iPad Air",
                "release_date": fake.date_between(start_date="-3y", end_date="today"),
            },
            {
                "name": "Умные часы",
                "model": "Watch Series 8",
                "release_date": fake.date_between(start_date="-1y", end_date="today"),
            },
            {
                "name": "Наушники",
                "model": "AirPods Pro",
                "release_date": fake.date_between(start_date="-2y", end_date="today"),
            },
        ]

        products = []
        for product_data in products_data:
            product = Product.objects.create(**product_data)
            products.append(product)

        return products

    def create_contacts(self, fake):
        """Создание контактов"""
        contacts = []
        for i in range(10):  # Создаем 10 контактов
            contact = Contact.objects.create(
                email=fake.unique.email(),
                country="Россия",
                city=fake.city(),
                street=fake.street_name(),
                house_number=fake.building_number(),
            )
            contacts.append(contact)

        return contacts

    def create_network_nodes(self, fake, contacts, products):
        """Создание узлов сети"""
        network_nodes = []
        contact_index = 0

        # Создаем заводы (уровень 0)
        factories = []
        for i in range(2):
            factory = NetworkNode.objects.create(
                name=f'Завод электроники "{fake.company()}"',
                node_type=NetworkNode.NodeType.FACTORY,
                contact=contacts[contact_index],
                debt=0,
            )
            factory.products.set(products[:3])
            factories.append(factory)
            network_nodes.append(factory)
            contact_index += 1

        # Создаем розничные сети (уровень 1)
        retail_networks = []
        for i in range(3):
            supplier = fake.random_element(factories)

            retail = NetworkNode.objects.create(
                name=f'Розничная сеть "{fake.company()}"',
                node_type=NetworkNode.NodeType.RETAIL,
                contact=contacts[contact_index],
                supplier=supplier,
                debt=fake.pydecimal(left_digits=6, right_digits=2, positive=True),
            )
            retail.products.set(products[1:4])
            retail_networks.append(retail)
            network_nodes.append(retail)
            contact_index += 1

        # Создаем индивидуальных предпринимателей (уровень 1 и 2)
        entrepreneurs = []
        suppliers = factories + retail_networks

        for i in range(4):
            supplier = fake.random_element(suppliers)

            entrepreneur = NetworkNode.objects.create(
                name=f"ИП {fake.last_name()} {fake.first_name()}",
                node_type=NetworkNode.NodeType.ENTREPRENEUR,
                contact=contacts[contact_index],
                supplier=supplier,
                debt=fake.pydecimal(left_digits=5, right_digits=2, positive=True),
            )
            entrepreneur.products.set([products[i % len(products)]])
            entrepreneurs.append(entrepreneur)
            network_nodes.append(entrepreneur)
            contact_index += 1

        return network_nodes
