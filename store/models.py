from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Jewelry product model with material, metal, stone, and size fields.
    """
    METAL_CHOICES = [
        ('gold_18k',    '18K Gold'),
        ('gold_14k',    '14K Gold'),
        ('gold_9k',     '9K Gold'),
        ('rose_gold',   'Rose Gold'),
        ('white_gold',  'White Gold'),
        ('silver_925',  'Sterling Silver (925)'),
        ('platinum',    'Platinum'),
        ('titanium',    'Titanium'),
        ('stainless',   'Stainless Steel'),
        ('other',       'Other'),
    ]
    STONE_CHOICES = [
        ('',             'No Stone'),
        ('diamond',      'Diamond'),
        ('ruby',         'Ruby'),
        ('emerald',      'Emerald'),
        ('sapphire',     'Sapphire'),
        ('pearl',        'Pearl'),
        ('amethyst',     'Amethyst'),
        ('opal',         'Opal'),
        ('topaz',        'Topaz'),
        ('garnet',       'Garnet'),
        ('turquoise',    'Turquoise'),
        ('morganite',    'Morganite'),
        ('cubic_zirconia','Cubic Zirconia'),
        ('other',        'Other'),
    ]

    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, blank=True)
    tagline     = models.CharField(max_length=300, blank=True)
    description = models.TextField()

    # Pricing
    price         = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Jewelry-specific fields
    metal       = models.CharField(max_length=20, choices=METAL_CHOICES, blank=True)
    stone       = models.CharField(max_length=20, choices=STONE_CHOICES, blank=True)
    stone_carat = models.CharField(max_length=50, blank=True, help_text="e.g. 0.5ct, 1ct total weight")
    weight_grams= models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Item weight in grams")
    dimensions  = models.CharField(max_length=100, blank=True, help_text="e.g. 18mm diameter, 45cm chain")
    sizes_available = models.CharField(max_length=200, blank=True, help_text="Comma-separated sizes, e.g. 5,6,7,8")
    hallmark    = models.CharField(max_length=100, blank=True, help_text="e.g. 925, 750, Pt950")
    is_customizable = models.BooleanField(default=False, help_text="Can be engraved or resized on request")

    # Inventory
    stock       = models.PositiveIntegerField(default=0)
    sku         = models.CharField(max_length=100, blank=True, unique=True, null=True)

    # Status
    is_featured = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_new_arrival = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def discount_percent(self):
        if self.compare_price and self.compare_price > self.price:
            return int((1 - self.price / self.compare_price) * 100)
        return None

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def size_list(self):
        if self.sizes_available:
            return [s.strip() for s in self.sizes_available.split(',')]
        return []

    def get_metal_display_label(self):
        return dict(self.METAL_CHOICES).get(self.metal, self.metal)

    def get_stone_display_label(self):
        return dict(self.STONE_CHOICES).get(self.stone, self.stone)


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='products/')
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} — image {self.id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('refunded',   'Refunded'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Credit / Debit Card (Stripe)'),
        ('paypal', 'PayPal'),
        ('cod',    'Cash on Delivery'),
        ('bank',   'Bank Transfer'),
    ]

    user            = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    # Customer info (stored at time of order — user may delete account)
    full_name       = models.CharField(max_length=150)
    email           = models.EmailField()
    phone           = models.CharField(max_length=30, blank=True)
    address_line1   = models.CharField(max_length=250)
    address_line2   = models.CharField(max_length=250, blank=True)
    city            = models.CharField(max_length=100)
    state           = models.CharField(max_length=100, blank=True)
    postal_code     = models.CharField(max_length=20)
    country         = models.CharField(max_length=100, default='United States')
    gift_note       = models.TextField(blank=True, help_text="Optional gift message")

    # Payment
    payment_method  = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_id      = models.CharField(max_length=300, blank=True, help_text="Stripe/PayPal transaction ID")
    is_paid         = models.BooleanField(default=False)

    # Totals
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.full_name}"

    @property
    def order_number(self):
        return f"AUR-{self.pk:05d}"


class OrderItem(models.Model):
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name= models.CharField(max_length=200)   # snapshot at time of order
    size        = models.CharField(max_length=20, blank=True)
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Cart(models.Model):
    """Session-based cart (works for both guests and logged-in users)."""
    session_key = models.CharField(max_length=40, unique=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.session_key}"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.cartitem_set.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart        = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    size        = models.CharField(max_length=20, blank=True)
    quantity    = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product', 'size')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity


class ContactMessage(models.Model):
    name         = models.CharField(max_length=100)
    email        = models.EmailField()
    subject      = models.CharField(max_length=200)
    message      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.name} — {self.subject}"
