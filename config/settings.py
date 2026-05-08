from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════════════════
# WHITE-LABEL SITE CONFIGURATION
# Edit ONLY this dict to fully rebrand your jewelry store.
# ═══════════════════════════════════════════════════════════════
SITE_CONFIG = {
    # ── Brand ──────────────────────────────────────────────────
    "SITE_NAME":        "Aurum & Co.",
    "SITE_TAGLINE":     "Wear what matters.",
    "SITE_DESCRIPTION": "Handcrafted fine jewelry for every chapter of your story.",

    # ── Logo ───────────────────────────────────────────────────
    # Leave "" to show text logo. Or set e.g. "images/logo.svg"
    "LOGO_URL":   "",
    "LOGO_WIDTH": "130px",

    # ── Colors (Dark mode) ─────────────────────────────────────
    "COLOR_PRIMARY":       "#0c0b09",   # Deep charcoal background
    "COLOR_SECONDARY":     "#161410",   # Card surfaces
    "COLOR_ACCENT":        "#c9a84c",   # Gold accent
    "COLOR_ACCENT_HOVER":  "#dbb85a",   # Gold hover
    "COLOR_TEXT":          "#f2ede4",   # Warm white text
    "COLOR_TEXT_MUTED":    "#8a8070",   # Muted text
    "COLOR_BORDER":        "#2a2520",   # Borders

    # ── Colors (Light mode) ────────────────────────────────────
    "COLOR_PRIMARY_LIGHT":      "#faf8f4",
    "COLOR_SECONDARY_LIGHT":    "#f0ece4",
    "COLOR_TEXT_LIGHT":         "#1a1510",
    "COLOR_TEXT_MUTED_LIGHT":   "#6a6050",
    "COLOR_BORDER_LIGHT":       "#ddd8cc",

    # ── Typography ─────────────────────────────────────────────
    "FONT_DISPLAY": "'Cormorant Garamond', Georgia, serif",
    "FONT_BODY":    "'Jost', system-ui, sans-serif",

    # ── Contact ────────────────────────────────────────────────
    "CONTACT_EMAIL":   "hello@aurumco.com",
    "CONTACT_PHONE":   "+1 (800) 000-0000",
    "CONTACT_ADDRESS": "5th Avenue, New York, NY 10011",

    # ── Social ─────────────────────────────────────────────────
    "SOCIAL_INSTAGRAM": "https://instagram.com/",
    "SOCIAL_TWITTER":   "",
    "SOCIAL_FACEBOOK":  "",
    "SOCIAL_PINTEREST": "https://pinterest.com/",

    # ── Footer ─────────────────────────────────────────────────
    "FOOTER_TAGLINE": "© 2025 Aurum & Co. All rights reserved.",
    "FOOTER_NOTE":    "Free shipping on orders over $150 · 30-day returns · Lifetime resize",
}

# ═══════════════════════════════════════════════════════════════
# PAYMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════
PAYMENT_CONFIG = {
    # ── Stripe ─────────────────────────────────────────────────
    # Get keys at: https://dashboard.stripe.com/apikeys
    "STRIPE_ENABLED":     True,
    "STRIPE_PUBLIC_KEY":  "pk_test_REPLACE_WITH_YOUR_STRIPE_PUBLIC_KEY",
    "STRIPE_SECRET_KEY":  "sk_test_REPLACE_WITH_YOUR_STRIPE_SECRET_KEY",
    "STRIPE_CURRENCY":    "usd",   # e.g. "usd", "eur", "gbp"

    # ── PayPal ─────────────────────────────────────────────────
    # Get client ID at: https://developer.paypal.com/dashboard/
    "PAYPAL_ENABLED":    True,
    "PAYPAL_CLIENT_ID":  "REPLACE_WITH_YOUR_PAYPAL_CLIENT_ID",
    "PAYPAL_CURRENCY":   "USD",
    "PAYPAL_SANDBOX":    True,   # Set False for live/production

    # ── Cash on Delivery ───────────────────────────────────────
    "COD_ENABLED":       True,
    "COD_LABEL":         "Cash on Delivery",
    "COD_NOTE":          "Pay in cash when your order arrives. Available for local deliveries.",

    # ── Bank Transfer ──────────────────────────────────────────
    "BANK_ENABLED":      False,
    "BANK_DETAILS":      "Account: 0000-0000 | Sort: 00-00-00 | Reference: your order number",

    # ── Free Shipping Threshold ────────────────────────────────
    "FREE_SHIPPING_ABOVE": 150,   # Set 0 to always charge shipping
    "SHIPPING_COST":        12,   # Flat shipping cost if below threshold
}

# ═══════════════════════════════════════════════════════════════
# FEATURED PRODUCT
# None = auto-pick (is_featured=True, then most recent)
# Integer = always use that product PK
# ═══════════════════════════════════════════════════════════════
FEATURED_PRODUCT_ID = None

# ─── Security ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-default-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'