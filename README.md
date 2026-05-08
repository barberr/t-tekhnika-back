# T Tekhnika Backend

DRF-бэкенд интернет-магазина бытовой техники с хранением категорий и товаров поставщика.

## Что уже есть

- каталог категорий поставщика с иерархией;
- товары поставщика, привязанные к категориям;
- REST API для чтения категорий, товаров, изображений, характеристик, складов, адресов и истории синхронизаций;
- management command для импорта данных из внешнего API поставщика;
- стандартная админка Django.

## Быстрый старт

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py createsuperuser
./.venv/bin/python manage.py runserver
```

## Настройка API поставщика

Настройки можно передать переменными окружения или положить в локальный файл `.env`.
Файл `.env` не хранится в git; за основу можно взять `.env.example`.

```bash
cp .env.example .env
```

После этого укажите реальные `SUPPLIER_API_BASE_URL`, `SUPPLIER_API_LOGIN` и `SUPPLIER_API_PASSWORD`.

Если поставщик отдает абсолютные URL, `SUPPLIER_API_BASE_URL` можно не задавать.

Для QuickFox-авторизации через логин/пароль:

```env
SUPPLIER_API_BASE_URL=https://supplier.example
SUPPLIER_API_LOGIN=ClientLogin
SUPPLIER_API_PASSWORD=ClientPassword
SUPPLIER_API_ENDPOINT=/api/2
SUPPLIER_AUTH_ENDPOINT=/api/2
```

При таких настройках клиент сначала отправляет `login`-запрос в QuickFox, сохраняет `session`, добавляет ее в последующие JSON-запросы и передает `Cookie: session=...` при запросе статики через `fetch_static()`.

Дерево категорий поставщик отдает как файл каталога, поэтому для него используется URL:

```env
SUPPLIER_CATEGORIES_URL=/download/catalog/json/catalog_tree_9.json
SUPPLIER_PRODUCTS_URL=/download/catalog/json/products_9.json
```

Клиент автоматически передаст `Cookie: session=...` для таких `/download/` URL.

`SUPPLIER_PRODUCTS_URL` может быть обычным URL или JSON-строкой тела запроса QuickFox, например:

```bash
export SUPPLIER_CATEGORIES_URL='{"data":{},"request":{"method":"categories","model":"catalog","module":"quickfox"}}'
```

Цены и остатки обновляются отдельным API-методом `get_active_products`; клиент сам добавляет `session` в запрос.
Также поддержаны каталоговые методы API 2.13:

- изображения товаров через `products_clients_images.read_new`;
- характеристики товаров 18+ через `get_adult_products_characteristics`;
- склады через `get_available_logistic_centers`;
- адреса через `get_addresses`.

## Импорт данных

```bash
./.venv/bin/python manage.py import_supplier_data --mode all
./.venv/bin/python manage.py import_supplier_data --mode categories
./.venv/bin/python manage.py import_supplier_data --mode products
```

Также можно передать URL прямо в команду:

```bash
./.venv/bin/python manage.py import_supplier_data \
  --mode all \
  --categories-url "https://supplier.example/api/categories/tree" \
  --products-url "https://supplier.example/api/products"
```

## Импорт из админки

В Django admin откройте раздел `Запуски синхронизации`. Над списком доступны действия:

- `Проверить API`;
- `Загрузить категории`;
- `Загрузить товары`;
- `Обновить цены и наличие`;
- `Загрузить изображения`;
- `Загрузить характеристики 18+`;
- `Загрузить склады`;
- `Загрузить адреса`;
- `Загрузить все`.

Результат операции появится в сообщении админки, а история загрузок сохраняется в `Запуски синхронизации`.

## API

- `GET /api/`
- `GET /api/categories/`
- `GET /api/products/`
- `GET /api/product-images/`
- `GET /api/adult-characteristics/`
- `GET /api/logistic-centers/`
- `GET /api/supplier-addresses/`
- `GET /api/sync-runs/`

Поддерживаемые фильтры:

- `/api/categories/?parent=null`
- `/api/categories/?parent=9839`
- `/api/categories/?is_leaf=true`
- `/api/products/?category=10059`
- `/api/products/?vendor=Transcend`
- `/api/products/?has_image=true`
- `/api/products/?sku=225436`
- `/api/products/?search=флешка`
- `/api/product-images/?sku=43950`
- `/api/product-images/?deleted=false`
- `/api/adult-characteristics/?sku=10524309`
