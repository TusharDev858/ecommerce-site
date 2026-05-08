"""
Management command: python manage.py seed_demo

Seeds the database with sample categories and products for development/demo purposes.
Safe to run multiple times — skips existing data.
"""
from django.core.management.base import BaseCommand
from store.models import Category, Product


DEMO_CATEGORIES = [
    {"name": "Accessories", "slug": "accessories"},
    {"name": "Home & Living", "slug": "home-living"},
    {"name": "Electronics", "slug": "electronics"},
    {"name": "Apparel", "slug": "apparel"},
]

DEMO_PRODUCTS = [
    {
        "name": "Artisan Leather Wallet",
        "slug": "artisan-leather-wallet",
        "category": "accessories",
        "tagline": "Full-grain leather, built to last a lifetime.",
        "description": "Crafted from premium full-grain Italian leather, this slim bifold wallet features 6 card slots, a bill compartment, and a hidden pocket.\n\nEach wallet is hand-stitched and individually inspected before shipping.",
        "price": 89.00, "compare_price": 120.00, "stock": 42, "is_featured": True,
    },
    {
        "name": "Ceramic Pour-Over Set",
        "slug": "ceramic-pour-over-set",
        "category": "home-living",
        "tagline": "Start your mornings with intention.",
        "description": "A beautifully crafted ceramic pour-over coffee set. Includes the dripper, carafe, and a stainless steel filter — no paper needed.\n\nHandmade in small batches with food-safe, lead-free glaze.",
        "price": 64.00, "compare_price": None, "stock": 18, "is_featured": False,
    },
    {
        "name": "Brass Desk Lamp",
        "slug": "brass-desk-lamp",
        "category": "home-living",
        "tagline": "Warm light, minimal footprint.",
        "description": "An architectural desk lamp with a solid brass arm and matte black base. Features a dimmer switch and standard E26 bulb compatibility.",
        "price": 145.00, "compare_price": 190.00, "stock": 7, "is_featured": False,
    },
    {
        "name": "Merino Wool Beanie",
        "slug": "merino-wool-beanie",
        "category": "apparel",
        "tagline": "Superfine Merino. Exceptionally soft.",
        "description": "Made from 100% extra-fine Merino wool. Naturally temperature-regulating, moisture-wicking, and odor-resistant.",
        "price": 38.00, "compare_price": None, "stock": 55, "is_featured": False,
    },
    {
        "name": "Oak Phone Stand",
        "slug": "oak-phone-stand",
        "category": "home-living",
        "tagline": "Solid oak, sustainably sourced.",
        "description": "A CNC-machined solid oak phone stand compatible with all phone sizes. Non-slip base and cable management groove.",
        "price": 29.00, "compare_price": None, "stock": 0, "is_featured": False,
    },
    {
        "name": "Titanium Pen",
        "slug": "titanium-pen",
        "category": "accessories",
        "tagline": "Write in titanium. Write forever.",
        "description": "A precision-machined titanium ballpoint pen accepting standard Parker-style refills. Lightweight at 28g yet virtually indestructible.",
        "price": 78.00, "compare_price": 95.00, "stock": 23, "is_featured": False,
    },
]


class Command(BaseCommand):
    help = "Seed database with demo categories and products"

    def handle(self, *args, **options):
        # Categories
        cats = {}
        for data in DEMO_CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=data["slug"], defaults={"name": data["name"]}
            )
            cats[data["slug"]] = cat
            self.stdout.write(f"  {'Created' if created else 'Exists '} category: {cat.name}")

        # Products
        for data in DEMO_PRODUCTS:
            cat_slug = data.pop("category")
            data["category"] = cats.get(cat_slug)
            product, created = Product.objects.get_or_create(
                slug=data["slug"], defaults=data
            )
            self.stdout.write(f"  {'Created' if created else 'Exists '} product: {product.name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {Category.objects.count()} categories, {Product.objects.count()} products."
        ))
