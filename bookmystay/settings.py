"""
Django settings for bookmystay project.
"""

from pathlib import Path
from django.contrib.messages import constants as messages

# ─── BASE ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-7mvlka7bl-_hi8fxs1y_*38b1+ne+%^+r-ai84qz^w#g)-rm6s'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# ─── APPS ───────────────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',                              # must be before admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # BookMyStay apps
    'users',
    'properties',
    'bookings',
    'payments',
    'reviews',
]

# ─── MIDDLEWARE ─────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookmystay.urls'

# ─── TEMPLATES ──────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookmystay.wsgi.application'

# ─── DATABASE ───────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── PASSWORD VALIDATION ────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── INTERNATIONALISATION ───────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Dar_es_Salaam'
USE_I18N      = True
USE_TZ        = True

# ─── STATIC & MEDIA ─────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── AUTH ───────────────────────────────────────────────
AUTH_USER_MODEL      = 'users.User'
LOGIN_URL            = '/users/login/'
LOGIN_REDIRECT_URL   = '/'
LOGOUT_REDIRECT_URL  = '/'

# ─── SESSION ────────────────────────────────────────────
SESSION_COOKIE_AGE         = 86400   # 1 day
SESSION_SAVE_EVERY_REQUEST = True

# ─── MESSAGES ───────────────────────────────────────────
MESSAGE_TAGS = {
    messages.DEBUG:   'debug',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'error',
}

# ─── DEFAULT PK ─────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── JAZZMIN ────────────────────────────────────────────
JAZZMIN_SETTINGS = {

    # Branding
    "site_title":   "BookMyStay Admin",
    "site_header":  "BookMyStay",
    "site_brand":   "BookMyStay",
    "welcome_sign": "Welcome to BookMyStay Admin Panel",
    "copyright":    "BookMyStay Tanzania © 2026",

    # Logo & Icon
    "site_icon": None,
    "site_logo": None,

    # Top nav links
    "topmenu_links": [
        {"name": "Dashboard",   "url": "admin:index"},
        {"name": "View Site",   "url": "/",             "new_window": True},
        {"name": "Properties",  "url": "/properties/",  "new_window": True},
    ],

    # User dropdown links
    "usermenu_links": [
        {"name": "View Site", "url": "/", "new_window": True},
    ],

    # Sidebar
    "show_sidebar":        True,
    "navigation_expanded": True,
    "hide_apps":           [],
    "hide_models":         [],

    # App & model order in sidebar
    "order_with_respect_to": [
        "users",
        "properties",
        "bookings",
        "payments",
        "reviews",
        "auth",
    ],

    # Model icons
    "icons": {
        # Users
        "users":                      "fas fa-users",
        "users.user":                 "fas fa-user",

        # Auth
        "auth":                       "fas fa-users-cog",
        "auth.group":                 "fas fa-layer-group",

        # Properties
        "properties.property":        "fas fa-building",
        "properties.propertyimage":   "fas fa-image",
        "properties.propertyextra":   "fas fa-concierge-bell",
        "properties.amenity":         "fas fa-wifi",
        "properties.propertyamenity": "fas fa-check-circle",

        # Bookings
        "bookings.booking":           "fas fa-calendar-check",
        "bookings.bookingextra":      "fas fa-receipt",
        "bookings.cart":              "fas fa-shopping-cart",
        "bookings.cartitem":          "fas fa-plus-circle",

        # Payments
        "payments.payment":           "fas fa-credit-card",

        # Reviews
        "reviews.review":             "fas fa-star",
    },

    "default_icon_parents":  "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Related modal popups
    "related_modal_active": True,

    # Custom assets
    "custom_css": None,
    "custom_js":  None,

    # Misc
    "use_google_fonts_cdn": True,
    "show_ui_builder":      False,
    "changeform_format":    "horizontal_tabs",

    "changeform_format_overrides": {
        "users.user":  "collapsible",
        "auth.group":  "vertical_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":        False,
    "footer_small_text":        False,
    "body_small_text":          False,
    "brand_small_text":         False,
    "brand_colour":             "navbar-dark",
    "accent":                   "accent-orange",
    "navbar":                   "navbar-dark",
    "no_navbar_border":         True,
    "navbar_fixed":             True,
    "layout_boxed":             False,
    "footer_fixed":             False,
    "sidebar_fixed":            True,
    "sidebar":                  "sidebar-dark-orange",
    "sidebar_nav_small_text":   False,
    "sidebar_disable_expand":   False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,
    "theme":                    "flatly",
    "dark_mode_theme":          "darkly",
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}