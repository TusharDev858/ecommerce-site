# Aurum & Co. — Jewelry E-Commerce Template
A luxury Django jewelry store with full payment integration.

## Quick Start
```bash
pip install django pillow stripe
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Visit http://127.0.0.1:8000 · Dashboard at /dashboard/

## Payment Setup

### Stripe (Card Payments)
1. Sign up at https://stripe.com
2. Go to Developers → API Keys
3. Copy your keys into `config/settings.py`:
```python
PAYMENT_CONFIG = {
    "STRIPE_ENABLED": True,
    "STRIPE_PUBLIC_KEY": "pk_test_...",
    "STRIPE_SECRET_KEY": "sk_test_...",
}
```

### PayPal
1. Go to https://developer.paypal.com/dashboard/
2. Create an app → copy Client ID
3. In `config/settings.py`:
```python
PAYMENT_CONFIG = {
    "PAYPAL_ENABLED": True,
    "PAYPAL_CLIENT_ID": "your-client-id",
    "PAYPAL_SANDBOX": True,   # False for live
}
```

### Cash on Delivery
Already enabled by default. Edit the label and note:
```python
PAYMENT_CONFIG = {
    "COD_ENABLED": True,
    "COD_LABEL": "Cash on Delivery",
    "COD_NOTE": "Pay when your order arrives.",
}
```

### Shipping Cost
```python
PAYMENT_CONFIG = {
    "FREE_SHIPPING_ABOVE": 150,  # 0 = always free
    "SHIPPING_COST": 12,
}
```

## Rebrand the Store
Edit only `SITE_CONFIG` in `config/settings.py`:
```python
SITE_CONFIG = {
    "SITE_NAME": "Your Jewelry Brand",
    "SITE_TAGLINE": "Your tagline here.",
    "COLOR_ACCENT": "#c9a84c",   # Change brand color
    "CONTACT_EMAIL": "hello@yourbrand.com",
    ...
}
```

## Jewelry Product Fields
Each product has: Metal, Stone, Stone Carat, Weight, Dimensions,
Sizes Available, Hallmark, Customizable flag, New Arrival flag.

## Demo Login
- **Superuser**: admin / admin123 ← Change in production!

## Key URLs
| URL | Page |
|-----|------|
| `/` | Storefront |
| `/cart/` | Shopping bag |
| `/checkout/` | Payment |
| `/dashboard/` | Admin dashboard |
| `/dashboard/product/add/` | Add product |
| `/orders/` | Customer order history |
| `/admin/` | Django admin |
