// ── Brewed & Co. — main.js ──

const cartDrawer = document.getElementById('cartDrawer');
const cartOverlay = document.getElementById('cartOverlay');
const cartClose = document.getElementById('cartClose');
const cartDrawerBody = document.getElementById('cartDrawerBody');
const cartDrawerFooter = document.getElementById('cartDrawerFooter');
const cartDrawerTotal = document.getElementById('cartDrawerTotal');

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function openCart() {
    cartDrawer.classList.add('active');
    cartOverlay.classList.add('active');
    loadCartData();
}

function closeCart() {
    cartDrawer.classList.remove('active');
    cartOverlay.classList.remove('active');
}

function loadCartData() {
    cartDrawerBody.innerHTML = '<div class="cart-drawer-loading">Loading...</div>';
    fetch('/cart/data')
        .then(res => res.json())
        .then(data => renderCart(data))
        .catch(() => {
            cartDrawerBody.innerHTML = '<p class="cart-drawer-loading">Failed to load cart.</p>';
        });
}

function renderCart(data) {
    if (data.items.length === 0) {
        cartDrawerBody.innerHTML = `
            <div class="cart-drawer-empty">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                    <line x1="3" y1="6" x2="21" y2="6"/>
                    <path d="M16 10a4 4 0 01-8 0"/>
                </svg>
                <p>Your cart is empty.</p>
                <a href="/shop" class="btn btn-accent btn-sm">Browse Products</a>
            </div>`;
        cartDrawerFooter.style.display = 'none';
        updateBadge(0);
        return;
    }

    let html = '';
    data.items.forEach(item => {
        const imageHtml = item.image_url
            ? `<img src="${item.image_url}" alt="${item.name}">`
            : `<div class="drawer-item-image-placeholder">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8h1a4 4 0 010 8h-1"/>
                    <path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/>
                    <line x1="6" y1="1" x2="6" y2="4"/>
                    <line x1="10" y1="1" x2="10" y2="4"/>
                    <line x1="14" y1="1" x2="14" y2="4"/>
                </svg>
               </div>`;

        html += `
        <div class="drawer-item" id="drawer-item-${item.id}">
            <div class="drawer-item-image">${imageHtml}</div>
            <div class="drawer-item-info">
                <div class="drawer-item-name">${item.name}</div>
                <div class="drawer-item-meta">$${item.price.toFixed(2)} each</div>
                <div class="drawer-qty-controls">
                    <button class="drawer-qty-btn" data-action="decrease" data-id="${item.id}">−</button>
                    <input class="drawer-qty-input" type="number" value="${item.quantity}" min="1" data-id="${item.id}">
                    <button class="drawer-qty-btn" data-action="increase" data-id="${item.id}">+</button>
                </div>
            </div>
            <div class="drawer-item-right">
                <div class="drawer-item-subtotal">$${item.subtotal.toFixed(2)}</div>
                <button class="drawer-item-remove" data-id="${item.id}" title="Remove">✕</button>
            </div>
        </div>`;
    });

    cartDrawerBody.innerHTML = html;
    cartDrawerTotal.textContent = `$${data.total.toFixed(2)}`;
    cartDrawerFooter.style.display = 'block';
    updateBadge(data.count);
    attachDrawerEvents();
}

function updateBadge(count) {
    let badge = document.querySelector('.cart-badge');
    if (count > 0) {
        if (!badge) {
            const navCart = document.querySelector('.nav-cart');
            badge = document.createElement('span');
            badge.className = 'cart-badge';
            navCart.appendChild(badge);
        }
        badge.textContent = count;
    } else {
        badge?.remove();
    }
}

function updateCartItem(itemId, quantity) {
    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `quantity=${quantity}&csrf_token=${getCsrfToken()}`
    }).then(() => loadCartData());
}

function removeCartItem(itemId) {
    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `csrf_token=${getCsrfToken()}`
    }).then(() => loadCartData());
}

function attachDrawerEvents() {
    // Quantity buttons
    document.querySelectorAll('.drawer-qty-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const input = document.querySelector(`.drawer-qty-input[data-id="${id}"]`);
            let qty = parseInt(input.value);
            if (btn.dataset.action === 'increase') qty++;
            if (btn.dataset.action === 'decrease') qty--;
            if (qty < 1) {
                removeCartItem(id);
                return;
            }
            input.value = qty;
            updateCartItem(id, qty);
        });
    });

    // Manual quantity input
    document.querySelectorAll('.drawer-qty-input').forEach(input => {
        input.addEventListener('change', () => {
            const qty = parseInt(input.value);
            if (qty < 1 || isNaN(qty)) {
                removeCartItem(input.dataset.id);
                return;
            }
            updateCartItem(input.dataset.id, qty);
        });
    });

    // Remove buttons
    document.querySelectorAll('.drawer-item-remove').forEach(btn => {
        btn.addEventListener('click', () => removeCartItem(btn.dataset.id));
    });
}

// ── Cart Page ──

function refreshCartPageTotals() {
    fetch('/cart/data')
        .then(res => res.json())
        .then(data => {
            updateBadge(data.count);
            data.items.forEach(item => {
                const subtotalEl = document.getElementById(`cart-subtotal-${item.id}`);
                if (subtotalEl) subtotalEl.textContent = `$${item.subtotal.toFixed(2)}`;

                const labelEl = document.getElementById(`summary-label-${item.id}`);
                if (labelEl) labelEl.textContent = `${item.name} × ${item.quantity}`;

                const summaryPriceEl = document.getElementById(`summary-price-${item.id}`);
                if (summaryPriceEl) summaryPriceEl.textContent = `$${item.subtotal.toFixed(2)}`;
            });
            const totalEl = document.getElementById('cart-page-total');
            if (totalEl) totalEl.textContent = `$${data.total.toFixed(2)}`;
        });
}

function updateCartItemOnPage(itemId, quantity) {
    fetch(`/cart/update/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `quantity=${quantity}&csrf_token=${getCsrfToken()}`
    }).then(() => refreshCartPageTotals());
}

function removeCartItemFromPage(itemId) {
    fetch(`/cart/remove/${itemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `csrf_token=${getCsrfToken()}`
    }).then(() => {
        document.getElementById(`cart-item-${itemId}`)?.remove();
        document.getElementById(`summary-row-${itemId}`)?.remove();
        fetch('/cart/data')
            .then(res => res.json())
            .then(data => {
                if (data.items.length === 0) {
                    window.location.reload(); // Show the empty state
                } else {
                    updateBadge(data.count);
                    const totalEl = document.getElementById('cart-page-total');
                    if (totalEl) totalEl.textContent = `$${data.total.toFixed(2)}`;
                }
            });
    });
}

function attachCartPageEvents() {
    document.querySelectorAll('.cart-page-qty-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const input = document.querySelector(`.cart-page-qty-input[data-id="${id}"]`);
            let qty = parseInt(input.value);
            if (btn.dataset.action === 'increase') qty++;
            if (btn.dataset.action === 'decrease') qty--;
            if (qty < 1) {
                removeCartItemFromPage(id);
                return;
            }
            input.value = qty;
            updateCartItemOnPage(id, qty);
        });
    });

    document.querySelectorAll('.cart-page-qty-input').forEach(input => {
        input.addEventListener('change', () => {
            const qty = parseInt(input.value);
            if (qty < 1 || isNaN(qty)) {
                removeCartItemFromPage(input.dataset.id);
                return;
            }
            updateCartItemOnPage(input.dataset.id, qty);
        });
    });

    document.querySelectorAll('.cart-page-remove').forEach(btn => {
        btn.addEventListener('click', () => removeCartItemFromPage(btn.dataset.id));
    });
}

// Initialize cart page events if on the cart page
if (document.getElementById('cartPageItems')) {
    attachCartPageEvents();
}

// ── Event Listeners ──

// Nav cart icon opens drawer
document.getElementById('navCartBtn')?.addEventListener('click', function (e) {
    e.preventDefault();
    openCart();
});

// Close on overlay click
cartOverlay?.addEventListener('click', closeCart);
cartClose?.addEventListener('click', closeCart);

// Close on Escape key
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeCart();
});

// Auto-open if ?cart=open in URL
if (new URLSearchParams(window.location.search).get('cart') === 'open') {
    openCart();
}