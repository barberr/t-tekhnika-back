from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    AdultProductCharacteristic,
    Category,
    LogisticCenter,
    SupplierAddress,
    SupplierProduct,
    SupplierProductImage,
    SupplierSyncRun,
)
from .serializers import (
    AdultProductCharacteristicSerializer,
    CategorySerializer,
    LogisticCenterSerializer,
    SupplierAddressSerializer,
    SupplierProductImageSerializer,
    SupplierProductSerializer,
    SupplierSyncRunSerializer,
)


@api_view(["GET"])
def api_root(_request):
    return Response(
        {
            "categories": "/api/categories/",
            "products": "/api/products/",
            "product-images": "/api/product-images/",
            "adult-characteristics": "/api/adult-characteristics/",
            "logistic-centers": "/api/logistic-centers/",
            "supplier-addresses": "/api/supplier-addresses/",
            "sync-runs": "/api/sync-runs/",
        }
    )


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.select_related("parent").all()
        parent_id = self.request.query_params.get("parent")
        is_leaf = self.request.query_params.get("is_leaf")
        search = self.request.query_params.get("search")

        if parent_id is not None:
            if parent_id == "null":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__supplier_id=parent_id)
        if is_leaf is not None:
            queryset = queryset.filter(is_leaf=is_leaf.lower() == "true")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class SupplierProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierProductSerializer

    def get_queryset(self):
        queryset = SupplierProduct.objects.select_related("category").all()
        category_id = self.request.query_params.get("category")
        vendor = self.request.query_params.get("vendor")
        has_image = self.request.query_params.get("has_image")
        search = self.request.query_params.get("search")
        sku = self.request.query_params.get("sku")

        if category_id:
            queryset = queryset.filter(category__supplier_id=category_id)
        if vendor:
            queryset = queryset.filter(vendor__icontains=vendor)
        if has_image is not None:
            queryset = queryset.filter(has_image=has_image.lower() == "true")
        if sku:
            queryset = queryset.filter(supplier_sku=sku)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class SupplierProductImageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SupplierProductImageSerializer

    def get_queryset(self):
        queryset = SupplierProductImage.objects.select_related("product").all()
        sku = self.request.query_params.get("sku")
        deleted = self.request.query_params.get("deleted")

        if sku:
            queryset = queryset.filter(supplier_sku=sku)
        if deleted is not None:
            queryset = queryset.filter(deleted=deleted.lower() == "true")
        return queryset


class AdultProductCharacteristicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdultProductCharacteristicSerializer

    def get_queryset(self):
        queryset = AdultProductCharacteristic.objects.select_related("product").all()
        sku = self.request.query_params.get("sku")

        if sku:
            queryset = queryset.filter(supplier_sku=sku)
        return queryset


class LogisticCenterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogisticCenter.objects.all()
    serializer_class = LogisticCenterSerializer


class SupplierAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupplierAddress.objects.all()
    serializer_class = SupplierAddressSerializer


class SupplierSyncRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SupplierSyncRun.objects.all()
    serializer_class = SupplierSyncRunSerializer
