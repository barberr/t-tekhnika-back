from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdultProductCharacteristicViewSet,
    CategoryViewSet,
    LogisticCenterViewSet,
    SupplierAddressViewSet,
    SupplierProductImageViewSet,
    SupplierProductViewSet,
    SupplierSyncRunViewSet,
    api_root,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", SupplierProductViewSet, basename="product")
router.register("product-images", SupplierProductImageViewSet, basename="product-image")
router.register("adult-characteristics", AdultProductCharacteristicViewSet, basename="adult-characteristic")
router.register("logistic-centers", LogisticCenterViewSet, basename="logistic-center")
router.register("supplier-addresses", SupplierAddressViewSet, basename="supplier-address")
router.register("sync-runs", SupplierSyncRunViewSet, basename="sync-run")

urlpatterns = [
    path("", api_root, name="api-root"),
    path("", include(router.urls)),
]
