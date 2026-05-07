# Brewed & Co. — Flask Web Shop

A full-stack e-commerce web application built with Python and Flask. Features a coffee and lifestyle product catalog, real-time cart drawer, Stripe payment integration with webhook-based order fulfillment, and a product management admin panel. Built with production-grade security practices throughout. - part of personal portfolio projects for bootcamp course.

## Features

- User authentication — register, login, logout with bcrypt password hashing
- Product catalog with category and subcategory filtering, anchor-based shop navigation
- Real-time slide-out cart drawer with AJAX quantity controls and live total updates
- Full cart page with inline stock enforcement and JS toast notifications
- Stripe Checkout integration with server-side price validation
- Webhook-based order fulfillment — orders only created after confirmed payment
- Stock management — server-side decrements after payment, pre-checkout validation
- Order history page with itemized order details
- Admin panel — add, edit, activate/deactivate products
- Security hardening — CSRF protection, webhook signature verification, idempotent order processing, open redirect prevention

## Requirements

- Python 3.10+
- Stripe account (test mode)
- Stripe CLI (for local webhook testing)
- Cloudinary account (for product image hosting)

## Installation

```
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```
FLASK_SECRET_KEY=your_secret_key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DEBUG=1
```

## How to Run

Start the Flask app:
```
python app.py
```

In a separate terminal, start the Stripe webhook listener:
```
stripe listen --forward-to 127.0.0.1:5000/webhook
```

The app runs at `http://localhost:5000`.

## Stripe Test Card

```
Card number: 4242 4242 4242 4242
Expiry: Any future date
CVC: Any 3 digits
```

## Project Structure

```
brewed-co/
├── app.py                  # App factory, extensions init, config
├── routes.py               # All route handlers and business logic
├── models.py               # SQLAlchemy models — User, Product, CartItem, Order, OrderItem
├── forms.py                # WTForms — RegisterForm, LoginForm, ProductForm
├── extensions.py           # Extension instances — db, login_manager, bcrypt, csrf
├── requirements.txt
├── .env                    # Environment variables
├── .gitignore
├── instance/
│   └── shop.db             # SQLite database (auto-generated on first run)
├── static/
│   ├── css/
│   │   └── style.css       # Full custom CSS — no frameworks
│   └── js/
│       └── main.js         # Cart drawer, AJAX cart updates, toast notifications
└── templates/
    ├── base.html           # Base layout — nav, cart drawer, flash messages, footer
    ├── home.html           # Landing page with hero and featured products
    ├── shop.html           # Product catalog with category sections and filter nav
    ├── product_detail.html # Individual product page
    ├── cart.html           # Full cart page with AJAX controls
    ├── checkout_success.html
    ├── checkout_cancel.html
    ├── orders.html         # Order history
    ├── login.html
    ├── register.html
    ├── admin_products.html # Product management table
    ├── add_product.html
    └── edit_product.html
```

## Security Notes

- Passwords hashed with bcrypt — never stored in plain text
- All state-changing routes protected with CSRF tokens
- Stripe webhook signature verified on every event before processing
- Order fulfillment is idempotent — duplicate webhook events are ignored
- Stock validated server-side before Stripe session creation and after payment
- Cart item ownership verified before any update or removal
- Open redirect prevented on login `next` parameter
- Admin routes protected with a custom `@admin_required` decorator
- `DEBUG` mode controlled via environment variable — never hardcoded

## Limitations

- SQLite used for development — swap to PostgreSQL for production
- No email confirmation on registration
- No password reset flow
- No account locking after n attempts
- Product images hosted on Cloudinary (external URLs only, no internal CMS or file upload)
- Single currency (USD)

## Author

Ghaleb Khadra