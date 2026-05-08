from django.core.management.base import BaseCommand

from catalog.services.supplier_api import SupplierAPIClient
from catalog.services.sync import run_supplier_sync


class Command(BaseCommand):
    help = "Импортирует категории и товары из API поставщика."

    def add_arguments(self, parser):
        parser.add_argument("--categories-url", dest="categories_url")
        parser.add_argument("--products-url", dest="products_url")
        parser.add_argument(
            "--mode",
            choices=("all", "categories", "products"),
            default="all",
        )

    def handle(self, *args, **options):
        mode = options["mode"]
        client = SupplierAPIClient()
        categories = None
        products = None

        if mode in ("all", "categories"):
            categories = client.fetch_categories(options.get("categories_url"))
        if mode in ("all", "products"):
            products = client.fetch_products(options.get("products_url"))

        sync_run = run_supplier_sync(mode=mode, categories=categories, products=products)
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completed: categories={sync_run.processed_categories}, "
                f"products={sync_run.processed_products}"
            )
        )
