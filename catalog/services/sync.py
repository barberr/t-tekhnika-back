from decimal import Decimal

from django.db import transaction

from catalog.models import (
    AdultProductCharacteristic,
    Category,
    LogisticCenter,
    SupplierAddress,
    SupplierProduct,
    SupplierProductImage,
    SupplierSyncRun,
)

CHILD_KEYS = ("children", "childrens", "items", "nodes")
BATCH_SIZE = 500


def _children_from_node(node):
    for key in CHILD_KEYS:
        value = node.get(key)
        if isinstance(value, list):
            return value
    return []


def _coerce_decimal(value):
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _chunks(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def import_categories(tree_data) -> int:
    nodes = tree_data if isinstance(tree_data, list) else tree_data.get("results", [])
    processed = 0

    def walk(node, parent=None, parents=None):
        nonlocal processed
        parents = parents or []
        children = _children_from_node(node)
        name = node["name"].strip()
        category, _ = Category.objects.update_or_create(
            supplier_id=node["id"],
            defaults={
                "parent": parent,
                "name": name,
                "is_leaf": bool(node.get("leaf", not children)),
                "level": len(parents),
                "path": " / ".join([*parents, name]),
                "raw_payload": node,
            },
        )
        processed += 1
        for child in children:
            walk(child, parent=category, parents=[*parents, name])

    with transaction.atomic():
        for node in nodes:
            walk(node)
    return processed


def import_products(product_data) -> int:
    items = product_data if isinstance(product_data, list) else product_data.get("results", [])
    processed = 0

    category_by_supplier_id = {
        category.supplier_id: category
        for category in Category.objects.filter(supplier_id__in={item["category"] for item in items})
    }

    for batch in _chunks(items, BATCH_SIZE):
        with transaction.atomic():
            for item in batch:
                category = category_by_supplier_id.get(item["category"])
                if category is None:
                    continue
                SupplierProduct.objects.update_or_create(
                    supplier_sku=item["sku"],
                    defaults={
                        "category": category,
                        "name": item.get("name", "").strip(),
                        "part": item.get("part", "").strip(),
                        "vendor": item.get("vendor", "").strip(),
                        "barcodes": item.get("barcodes", "").strip(),
                        "has_image": bool(item.get("has_image", False)),
                        "multiplicity": int(item.get("multiplicity") or 0),
                        "volume": _coerce_decimal(item.get("volume")),
                        "weight": _coerce_decimal(item.get("weight")),
                        "rrp": _coerce_decimal(item.get("rrp")),
                        "warranty": str(item.get("warranty", "")).strip(),
                        "raw_payload": item,
                    },
                )
                processed += 1
    return processed


def update_active_products(active_products) -> int:
    items = active_products if isinstance(active_products, list) else active_products.get("products", [])
    processed = 0

    for batch in _chunks(items, BATCH_SIZE):
        with transaction.atomic():
            for item in batch:
                updated = SupplierProduct.objects.filter(supplier_sku=item["sku"]).update(
                    price=_coerce_decimal(item.get("price")),
                    qty=str(item.get("qty", "")).strip(),
                    nearest_logistic_center_qty=str(item.get("nearest_logistic_center_qty", "")).strip(),
                    delivery_days=int(item["delivery_days"]) if item.get("delivery_days") not in (None, "") else None,
                    multiplicity=int(item.get("multiplicity") or 0),
                    cost_delivery=_coerce_decimal(item.get("cost_delivery")),
                    active_payload=item,
                )
                processed += updated
    return processed


def import_product_images(images) -> int:
    processed = 0
    product_by_sku = {
        product.supplier_sku: product
        for product in SupplierProduct.objects.filter(supplier_sku__in={item["sku"] for item in images})
    }

    for batch in _chunks(images, BATCH_SIZE):
        with transaction.atomic():
            for item in batch:
                SupplierProductImage.objects.update_or_create(
                    supplier_image_id=item["id"],
                    defaults={
                        "product": product_by_sku.get(item["sku"]),
                        "supplier_sku": item["sku"],
                        "url": item.get("url", ""),
                        "deleted": bool(item.get("deleted", False)),
                        "priority": int(item.get("priority") or 0),
                        "raw_payload": item,
                    },
                )
                processed += 1
    return processed


def import_adult_characteristics(characteristics) -> int:
    processed = 0
    product_by_sku = {
        product.supplier_sku: product
        for product in SupplierProduct.objects.filter(supplier_sku__in={item["sku"] for item in characteristics})
    }

    for batch in _chunks(characteristics, BATCH_SIZE):
        with transaction.atomic():
            for item in batch:
                AdultProductCharacteristic.objects.update_or_create(
                    supplier_sku=item["sku"],
                    defaults={
                        "product": product_by_sku.get(item["sku"]),
                        "characteristics": item.get("characteristics", []),
                        "raw_payload": item,
                    },
                )
                processed += 1
    return processed


def import_logistic_centers(centers) -> int:
    processed = 0

    with transaction.atomic():
        for item in centers:
            LogisticCenter.objects.update_or_create(
                supplier_id=item["id"],
                defaults={
                    "name": item.get("name", ""),
                    "raw_payload": item,
                },
            )
            processed += 1
    return processed


def import_addresses(addresses) -> int:
    processed = 0

    with transaction.atomic():
        for item in addresses:
            SupplierAddress.objects.update_or_create(
                supplier_id=item["id"],
                defaults={
                    "address": item.get("address", ""),
                    "raw_payload": item,
                },
            )
            processed += 1
    return processed


def run_supplier_sync(
    mode,
    categories=None,
    products=None,
    active_products=None,
    product_images=None,
    adult_characteristics=None,
    logistic_centers=None,
    addresses=None,
):
    sync_run = SupplierSyncRun.objects.create(mode=mode, status="running")
    try:
        if categories is not None:
            sync_run.processed_categories = import_categories(categories)
        if products is not None:
            sync_run.processed_products = import_products(products)
        if active_products is not None:
            sync_run.processed_products = update_active_products(active_products)
        if product_images is not None:
            sync_run.processed_products = import_product_images(product_images)
        if adult_characteristics is not None:
            sync_run.processed_products = import_adult_characteristics(adult_characteristics)
        if logistic_centers is not None:
            sync_run.processed_categories = import_logistic_centers(logistic_centers)
        if addresses is not None:
            sync_run.processed_categories = import_addresses(addresses)
        sync_run.status = "success"
        sync_run.error_message = ""
    except Exception as exc:
        sync_run.status = "failed"
        sync_run.error_message = str(exc)
        raise
    finally:
        sync_run.save(
            update_fields=[
                "status",
                "processed_categories",
                "processed_products",
                "error_message",
                "updated_at",
            ]
        )
    return sync_run
