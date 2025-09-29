# 🏪 Electronics Store Network

Django REST API для управления сетью по продаже электроники с иерархической структурой.

## 📊 О проекте

Веб-приложение с API-интерфейсом и админ-панелью для управления сетью по продаже электроники. Сеть представляет собой иерархическую структуру из трех уровней: завод, розничная сеть, индивидуальный предприниматель.

## 🏗️ Архитектура

### Модели данных
- **NetworkNode** - звено сети (завод, розничная сеть, ИП)
- **Contact** - контактная информация
- **Product** - информация о продуктах

### Иерархия сети
- Завод (уровень 0)
- Розничная сеть (уровень 1)
- Индивидуальный предприниматель (уровень 2)

## 🚀 Быстрый старт

### Предварительные требования
- Python 3.12+
- PostgreSQL
- Poetry (менеджер зависимостей)

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/karim-mir/Electronics-Store.git
cd Electronics-Store
```
2. **Установите зависимости**
```commandline
poetry install
```
3. **Настройте переменные окружения**
- Создайте файл .env в корне проекта:
```commandline
SECRET_KEY=your-secret-key
DB_NAME=electronics_store
DB_USER=your-username
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```
4. **Примените миграции**
```commandline
poetry run python manage.py migrate
```
5. **Создайте суперпользователя**
```
poetry run python manage.py createsuperuser
```
6. **Запустите сервер**
```commandline
poetry run python manage.py runserver
```
## 🔧 API Endpoints
### Network Nodes
- GET /api/v1/network-nodes/ - список всех узлов

- POST /api/v1/network-nodes/ - создание узла

- GET /api/v1/network-nodes/{id}/ - детали узла

- PUT /api/v1/network-nodes/{id}/ - обновление узла

- DELETE /api/v1/network-nodes/{id}/ - удаление узла

### Фильтрация
- GET /api/v1/network-nodes/?country=Россия - фильтр по стране

### Контакты и Продукты
- GET /api/v1/contacts/ - список контактов

- GET /api/v1/products/ - список продуктов

## 🛠️ Админ-панель
- Доступна по адресу: /admin/

### Возможности:

- Просмотр всех объектов сети

- Ссылки на поставщиков

- Фильтрация по городу

- Admin action для очистки задолженности

## 🧪 Тестирование
### Запуск всех тестов
```commandline
poetry run python manage.py test
```

### Запуск с покрытием
```commandline
poetry run coverage run manage.py test
poetry run coverage report -m
```

## 🔒 Безопасность
- Аутентификация требуется для доступа к API

- Валидация бизнес-правил на уровне моделей

- Запрет прямого обновления поля задолженности

## 📝 Бизнес-правила
- Завод не может иметь поставщика (уровень 0)

- Максимальная глубина иерархии - 2 уровня

- Запрещены циклические зависимости

- Задолженность не может быть отрицательной

## 👥 Разработчики
- Karim Mir