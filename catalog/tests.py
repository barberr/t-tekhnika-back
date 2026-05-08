import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from catalog.models import (
    AdultProductCharacteristic,
    Category,
    LogisticCenter,
    SupplierAddress,
    SupplierProduct,
    SupplierProductImage,
)
from catalog.services.supplier_api import SupplierAPIClient
from catalog.services.sync import (
    import_adult_characteristics,
    import_categories,
    import_logistic_centers,
    import_product_images,
    import_products,
    import_addresses,
    update_active_products,
)


class SupplierAPIClientTests(TestCase):
    def test_quickfox_login_and_api_request_adds_session(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse({"success": True, "data": []})

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
            endpoint="/api/2",
            auth_endpoint="/api/2",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            response = client.api_request(
                {
                    "data": {},
                    "request": {
                        "method": "categories",
                        "model": "catalog",
                        "module": "quickfox",
                    },
                }
            )

        login_payload = json.loads(requests[0].data.decode("utf-8"))
        api_payload = json.loads(requests[1].data.decode("utf-8"))

        self.assertTrue(response["success"])
        self.assertEqual(login_payload["request"]["method"], "login")
        self.assertEqual(login_payload["data"]["login"], "ClientLogin")
        self.assertEqual(api_payload["session"], "F123")

    def test_fetch_static_uses_session_cookie(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                if isinstance(self.payload, bytes):
                    return self.payload
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse(b"file-content")

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            content = client.fetch_static("/static/image.jpg")

        self.assertEqual(content, b"file-content")
        self.assertEqual(requests[1].headers["Cookie"], "session=F123")

    def test_fetch_categories_reads_download_json_with_session_cookie(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse(
                [
                    {
                        "id": 91,
                        "leaf": True,
                        "name": "кресла детские автомобильные",
                        "childrens": [],
                    }
                ]
            )

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            categories = client.fetch_categories("/download/catalog/json/catalog_tree_9.json")

        self.assertEqual(categories[0]["id"], 91)
        self.assertEqual(requests[1].headers["Cookie"], "session=F123")

    def test_fetch_products_reads_download_json_with_session_cookie(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse([{"sku": 2881306, "category": 747, "name": "HP ролик"}])

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            products = client.fetch_products("/download/catalog/json/products_9.json")

        self.assertEqual(products[0]["sku"], 2881306)
        self.assertEqual(requests[1].headers["Cookie"], "session=F123")

    def test_fetch_active_products_uses_platform_method(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse(
                {
                    "success": True,
                    "data": {
                        "products": [{"sku": 1586891, "price": 58.21, "qty": "***"}],
                        "total": 1,
                    },
                }
            )

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            products = client.fetch_active_products()

        api_payload = json.loads(requests[1].data.decode("utf-8"))

        self.assertEqual(products[0]["sku"], 1586891)
        self.assertEqual(api_payload["request"]["method"], "get_active_products")
        self.assertEqual(api_payload["session"], "F123")

    def test_fetch_product_images_uses_read_new_method(self):
        requests = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            return FakeResponse(
                {
                    "success": True,
                    "data": {
                        "product_images": [
                            {
                                "id": 2217386,
                                "sku": 43950,
                                "url": "product_images/with_watermark/472/4335472.jpg",
                                "deleted": False,
                                "priority": 100,
                            }
                        ],
                        "total": 1,
                    },
                }
            )

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            images = client.fetch_product_images([43950])

        api_payload = json.loads(requests[1].data.decode("utf-8"))

        self.assertEqual(images[0]["id"], 2217386)
        self.assertEqual(api_payload["request"]["method"], "read_new")
        self.assertEqual(api_payload["filter"][0]["operator"], "IN")

    def test_fetch_reference_methods(self):
        calls = []

        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                return FakeResponse({"success": True, "session": "F123"})
            payload = json.loads(request.data.decode("utf-8"))
            method = payload["request"]["method"]
            if method == "get_adult_products_characteristics":
                return FakeResponse(
                    {
                        "success": True,
                        "data": {
                            "adult_products_characteristics": [
                                {"sku": 10524309, "characteristics": [{"name": "Цвет", "value": "черный"}]}
                            ]
                        },
                    }
                )
            if method == "get_available_logistic_centers":
                return FakeResponse({"success": True, "data": {"logistic_centers": [{"id": 1, "name": "МСК"}]}})
            return FakeResponse({"success": True, "data": {"addresses": [{"id": 1, "address": "адрес1"}]}})

        client = SupplierAPIClient(
            base_url="https://supplier.example",
            login="ClientLogin",
            password="ClientPassword",
        )

        with patch("catalog.services.supplier_api.urlopen", fake_urlopen):
            characteristics = client.fetch_adult_product_characteristics()
            centers = client.fetch_logistic_centers()
            addresses = client.fetch_addresses()

        self.assertEqual(characteristics[0]["sku"], 10524309)
        self.assertEqual(centers[0]["name"], "МСК")
        self.assertEqual(addresses[0]["address"], "адрес1")


class SupplierAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(self.admin_user)

    def test_sync_run_changelist_has_supplier_actions(self):
        response = self.client.get(reverse("admin:catalog_suppliersyncrun_changelist"))

        self.assertContains(response, "Проверить API")
        self.assertContains(response, "Загрузить категории")
        self.assertContains(response, "Загрузить товары")
        self.assertContains(response, "Обновить цены и наличие")
        self.assertContains(response, "Загрузить изображения")
        self.assertContains(response, "Загрузить характеристики 18+")
        self.assertContains(response, "Загрузить склады")
        self.assertContains(response, "Загрузить адреса")
        self.assertContains(response, "Загрузить все")

    def test_check_supplier_api_action_logs_in(self):
        with patch("catalog.admin.SupplierAPIClient") as client_class:
            client_class.return_value.login.return_value = "F123456789"
            response = self.client.post(reverse("admin:catalog_suppliersyncrun_check_supplier_api"))

        self.assertRedirects(response, reverse("admin:catalog_suppliersyncrun_changelist"))
        client_class.return_value.login.assert_called_once_with()


class SupplierSyncTests(TestCase):
    def test_import_categories_and_products(self):
        categories_payload = [
            {
                "id": 9839,
                "leaf": False,
                "name": "Бытовая техника",
                "childrens": [
                    {
                        "id": 10059,
                        "leaf": True,
                        "name": "Флешки",
                    }
                ],
            }
        ]
        products_payload = [
            {
                "barcodes": "00760557821281,0760557821281",
                "category": 10059,
                "has_image": True,
                "multiplicity": 0,
                "name": "Флешка USB Transcend JetFlash 350",
                "part": "TS4GJF350",
                "sku": 224186,
                "vendor": "Transcend",
                "volume": 0.000075,
                "rrp": 5000,
                "warranty": "6",
                "weight": 0.02,
            }
        ]

        imported_categories = import_categories(categories_payload)
        imported_products = import_products(products_payload)

        self.assertEqual(imported_categories, 2)
        self.assertEqual(imported_products, 1)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(SupplierProduct.objects.count(), 1)
        self.assertEqual(SupplierProduct.objects.get().rrp, 5000)

    def test_update_active_products(self):
        category = Category.objects.create(supplier_id=747, name="Расходники")
        product = SupplierProduct.objects.create(
            supplier_sku=1586891,
            category=category,
            name="Ролик захвата",
        )

        processed = update_active_products(
            [
                {
                    "price": 58.21,
                    "qty": "***",
                    "nearest_logistic_center_qty": "**",
                    "sku": 1586891,
                    "delivery_days": 0,
                    "multiplicity": 1,
                }
            ]
        )

        product.refresh_from_db()

        self.assertEqual(processed, 1)
        self.assertEqual(product.price, Decimal("58.21"))
        self.assertEqual(product.qty, "***")
        self.assertEqual(product.nearest_logistic_center_qty, "**")
        self.assertEqual(product.delivery_days, 0)

    def test_import_extra_catalog_references(self):
        category = Category.objects.create(supplier_id=747, name="Расходники")
        SupplierProduct.objects.create(
            supplier_sku=43950,
            category=category,
            name="Товар с изображением",
        )

        imported_images = import_product_images(
            [
                {
                    "id": 2217386,
                    "sku": 43950,
                    "url": "product_images/with_watermark/472/4335472.jpg",
                    "deleted": False,
                    "priority": 100,
                }
            ]
        )
        imported_characteristics = import_adult_characteristics(
            [{"sku": 43950, "characteristics": [{"name": "Цвет", "value": "черный"}]}]
        )
        imported_centers = import_logistic_centers([{"id": 1, "name": "МСК"}])
        imported_addresses = import_addresses([{"id": 1, "address": "адрес1"}])

        self.assertEqual(imported_images, 1)
        self.assertEqual(imported_characteristics, 1)
        self.assertEqual(imported_centers, 1)
        self.assertEqual(imported_addresses, 1)
        self.assertEqual(SupplierProductImage.objects.count(), 1)
        self.assertEqual(AdultProductCharacteristic.objects.count(), 1)
        self.assertEqual(LogisticCenter.objects.count(), 1)
        self.assertEqual(SupplierAddress.objects.count(), 1)


class CatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        category = Category.objects.create(
            supplier_id=10059,
            name="Флешки",
            is_leaf=True,
            level=1,
            path="Бытовая техника / Флешки",
        )
        SupplierProduct.objects.create(
            supplier_sku=225436,
            category=category,
            name="Флешка USB Transcend JetFlash 350 (TS8GJF350)",
            part="TS8GJF350",
            vendor="Transcend",
            barcodes="00760557821274",
            has_image=True,
            warranty="6",
        )

    def test_product_list_filters_by_vendor(self):
        response = self.client.get("/api/products/", {"vendor": "trans"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_api_root_lists_extra_catalog_endpoints(self):
        response = self.client.get("/api/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("product-images", response.data)
        self.assertIn("adult-characteristics", response.data)
        self.assertIn("logistic-centers", response.data)
        self.assertIn("supplier-addresses", response.data)
