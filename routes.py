from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app
from extensions import db
from models import User, Product, CartItem, Order, OrderItem
from forms import RegisterForm, LoginForm, ProductForm
from functools import wraps
from urllib.parse import urlparse
from datetime import datetime
import stripe
import os


@app.context_processor
def inject_globals():
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    return {'cart_count': cart_count, 'current_year': datetime.now().year}


# SECURITY: custom decorator to protect admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    featured = Product.query.filter_by(is_active=True).limit(4).all()
    return render_template('home.html', featured=featured)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        # SECURITY: check duplicate email before creating user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        user = User()
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # SECURITY: same error message whether email or password is wrong
        # Never tell the potential attacker which one failed
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        # SECURITY: redirect to intended page after login
        next_page = request.args.get('next')
        if next_page and urlparse(next_page).netloc != '':
            next_page = None    # reject external URLS
        return redirect(next_page or url_for('home'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/shop')
def shop():
    products = Product.query.filter_by(is_active=True).all()
    return render_template('shop.html', products=products)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)


@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin_products.html', products=products)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=form.image_url.data,
            stock=form.stock.data,
            category=form.category.data,
            subcategory=form.subcategory.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('add_product.html', form=form)


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.image_url = form.image_url.data
        product.stock = form.stock.data
        product.category = form.category.data
        product.subcategory = form.subcategory.data
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('edit_product.html', form=form, product=product)


@app.route('/admin/products/toggle/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    flash('Product updated!', 'success')
    return redirect(url_for('admin_products'))


@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    # SECURITY: server-side stock check, never trust the client
    if product.stock < 1:
        flash('Sorry, this product is out of stock.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if cart_item:
        # SECURITY: check stock before incrementing
        if cart_item.quantity >= product.stock:
            flash('Not enough stock available.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))
        cart_item.quantity += 1
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=1
        )
        db.session.add(cart_item)

    db.session.commit()
    flash(f'{product.name} added to cart.', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    # SECURITY: ensure this cart item belongs to current user
    if cart_item.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('cart'))

    quantity = request.form.get('quantity', type=int)

    if not quantity or quantity < 1:
        db.session.delete(cart_item)
    elif quantity > cart_item.product.stock:
        cart_item.quantity = cart_item.product.stock
        flash(f'Only {cart_item.product.stock} items available. Quantity adjusted.', 'warning')
    else:
        cart_item.quantity = quantity

    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    # SECURITY: ensure this cart item belongs to current user
    if cart_item.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout')
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    # SECURITY: re-validate stock server-side before creating Stripe session
    for item in cart_items:
        if not item.product.is_active:
            flash(f'"{item.product.name}" is no longer available.', 'warning')
            return redirect(url_for('cart'))
        if item.product.stock < item.quantity:
            flash(f'"{item.product.name}" no longer has enough stock. Please update your cart.', 'warning')
            return redirect(url_for('cart'))

    # SECURITY: build line items server-side from DB prices
    # never trust prices sent from the client
    line_items = []
    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item.product.name,
                },
                # SECURITY: Stripe expects price in cents, convert here
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    # Create Stripe session with user_id in metadata
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        # Attach user_id as metadata so webhook knows whose cart to process
        metadata= {
            'user_id': current_user.id
        },
        success_url=url_for('checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=url_for('checkout_cancel', _external=True),
    )

    return redirect(session.url, code=303)


@app.route('/checkout/success')
@login_required
def checkout_success():
    return render_template('checkout_success.html')


@app.route('/checkout/cancel')
@login_required
def checkout_cancel():
    flash('Payment cancelled. Your cart has been saved.', 'warning')
    return redirect(url_for('cart'))


@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        # SECURITY: verify webhook signature before doing anything
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        # Invalid payload
        return '', 400
    except stripe.error.SignatureVerificationError:
        # SECURITY: reject requests that don't match Stripe's signature
        return '', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)

    return '', 200


def handle_successful_payment(session):
    # SECURITY: duplicate webhook protection - ignore duplicate webhook events
    existing_order = Order.query.filter_by(stripe_session_id=session['id']).first()
    if existing_order:
        return

    user_id = session['metadata']['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return

    total = sum(item.product.price * item.quantity for item in cart_items)

    # SECURITY: Order only created after confirmed payment
    order = Order(
        user_id=user_id,
        total=total,
        status='complete',
        stripe_session_id=session['id']
    )
    db.session.add(order)
    db.session.flush()

    # SECURITY: decrement stock server-side after confirmed payment
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.product.price
        )
        db.session.add(order_item)

        product = Product.query.get(item.product_id)
        if product:
            product.stock = max(0, product.stock - item.quantity)   # avoids weird artifacts (e.g. negative numbers) from showing up if for some reason, quantity exceeded stock - shouldn't but it's defensive coding

    # Clear the user's cart
    CartItem.query.filter_by(user_id=order.user_id).delete()

    db.session.commit()


@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)
