from rest_framework import serializers

from .models import (
    AdultProductCharacteristic,
    Category,
    LogisticCenter,
    SupplierAddress,
    SupplierProduct,
    SupplierProductImage,
    SupplierSyncRun,
)


class CategorySerializer(serializers.ModelSerializer):
    parent_supplier_id = serializers.IntegerField(source="parent.supplier_id", read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "supplier_id",
            "parent_supplier_id",
            "name",
            "is_leaf",
            "level",
            "path",
            "created_at",
            "updated_at",
        )


class SupplierProductSerializer(serializers.ModelSerializer):
    category_supplier_id = serializers.IntegerField(source="category.supplier_id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = SupplierProduct
        fields = (
            "id",
            "supplier_sku",
            "category_supplier_id",
            "category_name",
            "name",
            "part",
            "vendor",
            "barcodes",
            "has_image",
            "multiplicity",
            "volume",
            "weight",
            "rrp",
            "price",
            "qty",
            "nearest_logistic_center_qty",
            "delivery_days",
            "cost_delivery",
            "warranty",
            "last_synced_at",
        )


class SupplierProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProductImage
        fields = (
            "id",
            "supplier_image_id",
            "supplier_sku",
            "url",
            "deleted",
            "priority",
            "created_at",
            "updated_at",
        )


class AdultProductCharacteristicSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdultProductCharacteristic
        fields = (
            "id",
            "supplier_sku",
            "characteristics",
            "created_at",
            "updated_at",
        )


class LogisticCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogisticCenter
        fields = (
            "id",
            "supplier_id",
            "name",
            "created_at",
            "updated_at",
        )


class SupplierAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAddress
        fields = (
            "id",
            "supplier_id",
            "address",
            "created_at",
            "updated_at",
        )


class SupplierSyncRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierSyncRun
        fields = (
            "id",
            "mode",
            "status",
            "processed_categories",
            "processed_products",
            "error_message",
            "created_at",
            "updated_at",
        )
