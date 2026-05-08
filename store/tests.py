from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Product, Category, ContactMessage


class StoreViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Test Cat", slug="test-cat")
        self.product = Product.objects.create(
            name="Test Product", slug="test-product",
            category=self.cat, price=25.00, stock=10,
            description="A test product.", is_active=True, is_featured=True
        )
        self.superuser = User.objects.create_superuser(
            username="admin", password="pass", email="a@a.com"
        )
        self.user = User.objects.create_user(username="user", password="pass")

    def test_homepage_loads(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Product")

    def test_product_detail(self):
        r = self.client.get(reverse("product_detail", args=["test-product"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Product")

    def test_search(self):
        r = self.client.get("/?q=test")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Product")

    def test_search_no_results(self):
        r = self.client.get("/?q=zzznomatch")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "No products found")

    def test_category_filter(self):
        r = self.client.get("/?category=test-cat")
        self.assertEqual(r.status_code, 200)

    def test_register_and_login(self):
        r = self.client.post(reverse("register"), {
            "username": "newuser", "email": "n@n.com",
            "password1": "StrongPass999!", "password2": "StrongPass999!"
        })
        self.assertRedirects(r, reverse("home"))

    def test_login_view(self):
        r = self.client.post(reverse("login"), {
            "username": "user", "password": "pass"
        })
        self.assertRedirects(r, reverse("home"))

    def test_logout(self):
        self.client.login(username="user", password="pass")
        r = self.client.get(reverse("logout"))
        self.assertRedirects(r, reverse("home"))

    def test_dashboard_requires_superuser(self):
        self.client.login(username="user", password="pass")
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 302)

    def test_dashboard_accessible_to_superuser(self):
        self.client.login(username="admin", password="pass")
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Test Product")

    def test_contact_form_submission(self):
        r = self.client.post(reverse("home"), {
            "contact_submit": "1",
            "name": "Alice", "email": "alice@example.com",
            "subject": "Hello", "message": "A test message."
        }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(name="Alice").exists())

    def test_product_toggle(self):
        self.client.login(username="admin", password="pass")
        self.client.get(reverse("product_toggle", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_inactive_product_hidden(self):
        self.product.is_active = False
        self.product.save()
        r = self.client.get(reverse("product_detail", args=["test-product"]))
        self.assertEqual(r.status_code, 404)

    def test_product_add_superuser(self):
        self.client.login(username="admin", password="pass")
        r = self.client.get(reverse("product_add"))
        self.assertEqual(r.status_code, 200)

    def test_product_edit_superuser(self):
        self.client.login(username="admin", password="pass")
        r = self.client.get(reverse("product_edit", args=[self.product.pk]))
        self.assertEqual(r.status_code, 200)

    def test_product_add_blocked_for_regular_user(self):
        self.client.login(username="user", password="pass")
        r = self.client.get(reverse("product_add"))
        self.assertEqual(r.status_code, 302)

    def test_messages_view(self):
        self.client.login(username="admin", password="pass")
        r = self.client.get(reverse("messages"))
        self.assertEqual(r.status_code, 200)

    def test_discount_percent(self):
        self.product.compare_price = 50.00
        self.product.price = 25.00
        self.product.save()
        self.assertEqual(self.product.discount_percent, 50)

    def test_in_stock_property(self):
        self.assertTrue(self.product.in_stock)
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.in_stock)

    def test_product_slug_auto_generated(self):
        p = Product.objects.create(
            name="Auto Slug Product", price=10.00, stock=5,
            description="Test", is_active=True
        )
        self.assertEqual(p.slug, "auto-slug-product")
