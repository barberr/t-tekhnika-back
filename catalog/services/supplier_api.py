import json
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings


class SupplierAPIError(Exception):
    pass


def _looks_like_json(value):
    return isinstance(value, str) and value.strip().startswith(("{", "["))


def _is_static_download(url):
    return isinstance(url, str) and url.lstrip("/").startswith("download/")


def _unwrap_response_data(response):
    if isinstance(response, dict) and "data" in response:
        return response["data"]
    return response


class SupplierAPIClient:
    def __init__(
        self,
        base_url=None,
        token=None,
        login=None,
        password=None,
        endpoint=None,
        auth_endpoint=None,
        timeout=None,
    ):
        self.base_url = (base_url or settings.SUPPLIER_API_BASE_URL).rstrip("/")
        self.token = token if token is not None else settings.SUPPLIER_API_TOKEN
        self.login_name = login if login is not None else settings.SUPPLIER_API_LOGIN
        self.password = password if password is not None else settings.SUPPLIER_API_PASSWORD
        self.endpoint = endpoint or settings.SUPPLIER_API_ENDPOINT
        self.auth_endpoint = auth_endpoint or settings.SUPPLIER_AUTH_ENDPOINT
        self.timeout = timeout or settings.SUPPLIER_HTTP_TIMEOUT
        self.session = None

    def build_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if not self.base_url:
            return url
        return urljoin(f"{self.base_url}/", url.lstrip("/"))

    def _open_json(self, url, payload):
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            self.build_url(url),
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def login(self, force=False):
        if self.session and not force:
            return self.session
        if not self.login_name or not self.password:
            raise SupplierAPIError("SUPPLIER_API_LOGIN and SUPPLIER_API_PASSWORD are required")

        payload = {
            "data": {
                "login": self.login_name,
                "password": self.password,
            },
            "request": {
                "method": "login",
                "model": "auth",
                "module": "quickfox",
            },
        }
        response = self._open_json(self.auth_endpoint, payload)
        if not response.get("success"):
            message = response.get("message") or response.get("error") or "Supplier authentication failed"
            raise SupplierAPIError(message)
        session = response.get("session")
        if not session:
            raise SupplierAPIError("Supplier authentication response does not contain session")
        self.session = session
        return session

    def api_request(self, payload):
        if not isinstance(payload, dict):
            raise TypeError("QuickFox API payload must be a dict")
        request_payload = dict(payload)
        request_payload["session"] = self.login()
        response = self._open_json(self.endpoint, request_payload)
        if response.get("success") is False:
            message = response.get("message") or response.get("error") or "Supplier API request failed"
            raise SupplierAPIError(message)
        return response

    def fetch_json(self, url: str):
        if isinstance(url, dict):
            return self.api_request(url)
        if _looks_like_json(url):
            return self.api_request(json.loads(url))

        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.build_url(url), headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_static(self, url: str):
        headers = {}
        if self.login_name and self.password:
            headers["Cookie"] = f"session={self.login()}"
        request = Request(self.build_url(url), headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            return response.read()

    def fetch_static_json(self, url: str):
        return json.loads(self.fetch_static(url).decode("utf-8"))

    def fetch_categories(self, url=None):
        target = url or settings.SUPPLIER_CATEGORIES_URL
        if not target:
            raise ValueError("SUPPLIER_CATEGORIES_URL is not configured")
        if _is_static_download(target):
            return self.fetch_static_json(target)
        return _unwrap_response_data(self.fetch_json(target))

    def fetch_products(self, url=None):
        target = url or settings.SUPPLIER_PRODUCTS_URL
        if not target:
            raise ValueError("SUPPLIER_PRODUCTS_URL is not configured")
        if _is_static_download(target):
            return self.fetch_static_json(target)
        return _unwrap_response_data(self.fetch_json(target))

    def fetch_active_products(self, filters=None, data=None):
        payload = {
            "request": {
                "method": "get_active_products",
                "model": "client_api",
                "module": "platform",
            },
        }
        if filters:
            payload["filter"] = filters
        if data:
            payload["data"] = data
        response = self.api_request(payload)
        products = response.get("data", {}).get("products", [])
        if not isinstance(products, list):
            raise SupplierAPIError("Supplier active products response does not contain products list")
        return products

    def fetch_product_images(self, skus):
        if not skus:
            return []
        operator = "IN" if isinstance(skus, (list, tuple, set)) else "="
        value = list(skus) if operator == "IN" else skus
        response = self.api_request(
            {
                "filter": [
                    {
                        "operator": operator,
                        "property": "sku",
                        "value": value,
                    }
                ],
                "request": {
                    "method": "read_new",
                    "model": "products_clients_images",
                    "module": "platform",
                },
            }
        )
        return response.get("data", {}).get("product_images", [])

    def fetch_adult_product_characteristics(self):
        response = self.api_request(
            {
                "request": {
                    "method": "get_adult_products_characteristics",
                    "model": "client_api",
                    "module": "platform",
                },
            }
        )
        return response.get("data", {}).get("adult_products_characteristics", [])

    def fetch_logistic_centers(self):
        response = self.api_request(
            {
                "request": {
                    "method": "get_available_logistic_centers",
                    "model": "client_api",
                    "module": "platform",
                },
            }
        )
        return response.get("data", {}).get("logistic_centers", [])

    def fetch_addresses(self):
        response = self.api_request(
            {
                "request": {
                    "method": "get_addresses",
                    "model": "client_api",
                    "module": "platform",
                },
            }
        )
        return response.get("data", {}).get("addresses", [])
