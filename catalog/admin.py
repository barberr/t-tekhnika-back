import time

from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html

from .models import (
    AdultProductCharacteristic,
    Category,
    LogisticCenter,
    SupplierAddress,
    SupplierProduct,
    SupplierProductImage,
    SupplierSyncRun,
)
from .services.supplier_api import SupplierAPIClient
from .services.sync import run_supplier_sync

IMAGE_SKU_BATCH_SIZE = 100


def _chunks(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("supplier_id", "name", "parent", "is_leaf", "level")
    list_filter = ("is_leaf", "level")
    search_fields = ("name", "supplier_id")


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = (
        "supplier_sku",
        "name",
        "vendor",
        "category",
        "price",
        "rrp",
        "qty",
        "nearest_logistic_center_qty",
        "delivery_days",
        "has_image",
    )
    list_filter = ("has_image", "vendor", "delivery_days")
    search_fields = ("name", "part", "vendor", "supplier_sku", "barcodes")
    autocomplete_fields = ("category",)


@admin.register(SupplierProductImage)
class SupplierProductImageAdmin(admin.ModelAdmin):
    list_display = ("supplier_image_id", "supplier_sku", "url", "deleted", "priority")
    list_filter = ("deleted",)
    search_fields = ("supplier_sku", "url")
    autocomplete_fields = ("product",)


@admin.register(AdultProductCharacteristic)
class AdultProductCharacteristicAdmin(admin.ModelAdmin):
    list_display = ("supplier_sku", "updated_at")
    search_fields = ("supplier_sku",)
    autocomplete_fields = ("product",)


@admin.register(LogisticCenter)
class LogisticCenterAdmin(admin.ModelAdmin):
    list_display = ("supplier_id", "name")
    search_fields = ("name", "supplier_id")


@admin.register(SupplierAddress)
class SupplierAddressAdmin(admin.ModelAdmin):
    list_display = ("supplier_id", "address")
    search_fields = ("address", "supplier_id")


@admin.register(SupplierSyncRun)
class SupplierSyncRunAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/suppliersyncrun/change_list.html"
    list_display = (
        "created_at",
        "mode",
        "status",
        "processed_categories",
        "processed_products",
        "short_error_message",
    )
    list_filter = ("mode", "status")
    readonly_fields = (
        "created_at",
        "updated_at",
        "processed_categories",
        "processed_products",
        "error_message",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "check-supplier-api/",
                self.admin_site.admin_view(self.check_supplier_api),
                name="catalog_suppliersyncrun_check_supplier_api",
            ),
            path(
                "import-categories/",
                self.admin_site.admin_view(self.import_categories),
                name="catalog_suppliersyncrun_import_categories",
            ),
            path(
                "import-products/",
                self.admin_site.admin_view(self.import_products),
                name="catalog_suppliersyncrun_import_products",
            ),
            path(
                "update-active-products/",
                self.admin_site.admin_view(self.update_active_products),
                name="catalog_suppliersyncrun_update_active_products",
            ),
            path(
                "import-product-images/",
                self.admin_site.admin_view(self.import_product_images),
                name="catalog_suppliersyncrun_import_product_images",
            ),
            path(
                "import-adult-characteristics/",
                self.admin_site.admin_view(self.import_adult_characteristics),
                name="catalog_suppliersyncrun_import_adult_characteristics",
            ),
            path(
                "import-logistic-centers/",
                self.admin_site.admin_view(self.import_logistic_centers),
                name="catalog_suppliersyncrun_import_logistic_centers",
            ),
            path(
                "import-addresses/",
                self.admin_site.admin_view(self.import_addresses),
                name="catalog_suppliersyncrun_import_addresses",
            ),
            path(
                "import-all/",
                self.admin_site.admin_view(self.import_all),
                name="catalog_suppliersyncrun_import_all",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Ошибка")
    def short_error_message(self, obj):
        if not obj.error_message:
            return "-"
        return format_html("<span title='{}'>{}</span>", obj.error_message, obj.error_message[:120])

    def _redirect_to_changelist(self):
        return redirect("admin:catalog_suppliersyncrun_changelist")

    def check_supplier_api(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            session = SupplierAPIClient().login()
        except Exception as exc:
            self.message_user(request, f"Ошибка подключения к API поставщика: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Подключение к API поставщика работает. Session: {session[:8]}...",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_categories(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            client = SupplierAPIClient()
            categories = client.fetch_categories()
            sync_run = run_supplier_sync(mode="categories", categories=categories)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки категорий: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Категории загружены: {sync_run.processed_categories}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_products(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            client = SupplierAPIClient()
            products = client.fetch_products()
            sync_run = run_supplier_sync(mode="products", products=products)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки товаров: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Товары загружены: {sync_run.processed_products}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def update_active_products(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            client = SupplierAPIClient()
            active_products = client.fetch_active_products()
            sync_run = run_supplier_sync(mode="active_products", active_products=active_products)
        except Exception as exc:
            self.message_user(request, f"Ошибка обновления цен и наличия: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Цены и наличие обновлены для товаров: {sync_run.processed_products}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_product_images(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            client = SupplierAPIClient()
            skus = list(SupplierProduct.objects.filter(has_image=True).values_list("supplier_sku", flat=True))
            images = []
            for batch in _chunks(skus, IMAGE_SKU_BATCH_SIZE):
                images.extend(client.fetch_product_images(batch))
                time.sleep(0.6)
            sync_run = run_supplier_sync(mode="product_images", product_images=images)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки изображений: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Изображения загружены: {sync_run.processed_products}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_adult_characteristics(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            characteristics = SupplierAPIClient().fetch_adult_product_characteristics()
            sync_run = run_supplier_sync(mode="adult_characteristics", adult_characteristics=characteristics)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки характеристик 18+: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Характеристики 18+ загружены: {sync_run.processed_products}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_logistic_centers(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            centers = SupplierAPIClient().fetch_logistic_centers()
            sync_run = run_supplier_sync(mode="logistic_centers", logistic_centers=centers)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки складов: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Склады загружены: {sync_run.processed_categories}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_addresses(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            addresses = SupplierAPIClient().fetch_addresses()
            sync_run = run_supplier_sync(mode="addresses", addresses=addresses)
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки адресов: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                f"Адреса загружены: {sync_run.processed_categories}",
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()

    def import_all(self, request):
        if request.method != "POST":
            return self._redirect_to_changelist()
        try:
            client = SupplierAPIClient()
            categories = client.fetch_categories()
            products = client.fetch_products()
            active_products = client.fetch_active_products()
            sync_run = run_supplier_sync(
                mode="all",
                categories=categories,
                products=products,
                active_products=active_products,
            )
        except Exception as exc:
            self.message_user(request, f"Ошибка загрузки данных: {exc}", level=messages.ERROR)
        else:
            self.message_user(
                request,
                (
                    f"Данные загружены: категории={sync_run.processed_categories}, "
                    f"товары={sync_run.processed_products}"
                ),
                level=messages.SUCCESS,
            )
        return self._redirect_to_changelist()
