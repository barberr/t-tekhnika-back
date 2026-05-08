from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    supplier_id = models.PositiveIntegerField(unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    is_leaf = models.BooleanField(default=False)
    level = models.PositiveSmallIntegerField(default=0)
    path = models.CharField(max_length=1024, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["path", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class SupplierProduct(TimeStampedModel):
    supplier_sku = models.PositiveIntegerField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=500)
    part = models.CharField(max_length=128, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    barcodes = models.TextField(blank=True)
    has_image = models.BooleanField(default=False)
    multiplicity = models.PositiveIntegerField(default=0)
    volume = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    weight = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    rrp = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    qty = models.CharField(max_length=16, blank=True)
    nearest_logistic_center_qty = models.CharField(max_length=16, blank=True)
    delivery_days = models.PositiveIntegerField(null=True, blank=True)
    cost_delivery = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warranty = models.CharField(max_length=64, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    active_payload = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "supplier_sku"]
        verbose_name = "Товар поставщика"
        verbose_name_plural = "Товары поставщика"

    def __str__(self) -> str:
        return f"{self.name} ({self.supplier_sku})"


class SupplierProductImage(TimeStampedModel):
    supplier_image_id = models.PositiveIntegerField(unique=True)
    product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
    )
    supplier_sku = models.PositiveIntegerField(db_index=True)
    url = models.CharField(max_length=1024)
    deleted = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["supplier_sku", "-priority", "supplier_image_id"]
        verbose_name = "Изображение товара поставщика"
        verbose_name_plural = "Изображения товаров поставщика"

    def __str__(self) -> str:
        return f"{self.supplier_sku}: {self.url}"


class AdultProductCharacteristic(TimeStampedModel):
    product = models.OneToOneField(
        SupplierProduct,
        on_delete=models.CASCADE,
        related_name="adult_characteristics",
        null=True,
        blank=True,
    )
    supplier_sku = models.PositiveIntegerField(unique=True)
    characteristics = models.JSONField(default=list, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["supplier_sku"]
        verbose_name = "Характеристики товара 18+"
        verbose_name_plural = "Характеристики товаров 18+"

    def __str__(self) -> str:
        return str(self.supplier_sku)


class LogisticCenter(TimeStampedModel):
    supplier_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=255)
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["supplier_id"]
        verbose_name = "Склад поставщика"
        verbose_name_plural = "Склады поставщика"

    def __str__(self) -> str:
        return self.name


class SupplierAddress(TimeStampedModel):
    supplier_id = models.PositiveIntegerField(unique=True)
    address = models.TextField()
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["supplier_id"]
        verbose_name = "Адрес поставщика"
        verbose_name_plural = "Адреса поставщика"

    def __str__(self) -> str:
        return self.address


class SupplierSyncRun(TimeStampedModel):
    STATUS_CHOICES = [
        ("running", "running"),
        ("success", "success"),
        ("failed", "failed"),
    ]

    mode = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="running")
    processed_categories = models.PositiveIntegerField(default=0)
    processed_products = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запуск синхронизации"
        verbose_name_plural = "Запуски синхронизации"

    def __str__(self) -> str:
        return f"{self.mode} {self.status} {self.created_at:%Y-%m-%d %H:%M:%S}"
