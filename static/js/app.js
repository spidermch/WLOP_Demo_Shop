/* WLOP Explorer - Client-Side Application */
(function(){

// ================ STATE ================
var state = {
    configured: false,
    shopView: 'catalog', // catalog, cart, checkout, processing, result
    cart: [],
    apiLogs: [],
    paymentToken: null,    // hc_id or payment_id
    paymentResult: null,
    paymentFlow: 'hostedcheckout', // hostedcheckout or s2s
    currentPaymentId: null,
    currentOrderId: null,
    products: [],
    customers: [],
    customerDetailId: null,
    checkoutDetails: { name: '', email: '', address: '', city: '', zip: '', country: '', phone: '' },
};

function $(id) { return document.getElementById(id); }
function esc(s) { var d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
function fmt(v, c) { return (c || 'EUR') + ' ' + (v / 100).toFixed(2); }
function fmtTime(iso) { try { return new Date(iso).toLocaleTimeString(); } catch(e) { return iso; } }
function syntaxHL(obj) {
    if (!obj) return '';
    var s = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
        .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
        .replace(/: null/g, ': <span class="json-null">null</span>');
}
async function api(url, opts) {
    var r = await fetch(url, opts || {});
    var d = await r.json().catch(function() { return {}; });
    return { ok: r.ok, status: r.status, data: d };
}

// ================ TABS ================
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.toggle('active', b.dataset.tab === tab); });
    document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.toggle('active', c.id === 'tab-' + tab); });
    if (tab === 'products') loadProducts();
    if (tab === 'orders') refreshOrders();
    if (tab === 'customers') loadCustomers();
    if (tab === 'code' && !codeState.currentFile) loadCode('app.py', document.querySelector('[data-file="app.py"]'));
}
document.querySelectorAll('.tab-btn').forEach(function(b) { b.addEventListener('click', function() { switchTab(b.dataset.tab); }); });

// ================ SHOPPER VIEW ================
function renderShopper() {
    var el = $('shopper-content');
    if (state.shopView === 'catalog') { renderCatalog(el); return; }
    if (state.shopView === 'cart') { renderCart(el); return; }
    if (state.shopView === 'customer_details') { renderCustomerDetails(el); return; }
    if (state.shopView === 'checkout') { renderCheckout(el); return; }
    if (state.shopView === 'processing') {
        el.innerHTML = '<div class="processing-view"><div class="processing-spinner"></div><p>Processing payment...</p><p class="dev-hint">The customer is on the Worldline payment page.</p></div>';
        return;
    }
    if (state.shopView === 'result') { renderResult(el); return; }
}

function renderCatalog(el) {
    var h = '<div class="shop-nav"><h3>Shop</h3>';
    h += '<button class="cart-toggle" onclick="state.shopView=\'cart\';renderShopper()">Cart (' + state.cart.length + ')</button></div>';
    h += '<div class="product-grid">';
    state.products.forEach(function(p) {
        if (!p.active) return;
        h += '<div class="product-card"><div class="product-icon">' + p.icon + '</div>';
        h += '<div class="product-name">' + esc(p.name) + '</div>';
        h += '<div class="product-desc">' + esc(p.description) + '</div>';
        h += '<div class="product-price">' + fmt(p.price, p.currency) + '</div>';
        h += '<button class="btn btn-primary" onclick="addToCart(\'' + p.id + '\')">Add to Cart</button></div>';
    });
    h += '</div>';
    el.innerHTML = h;
}

function addToCart(pid) {
    var p = state.products.find(function(x) { return x.id === pid; });
    if (p) state.cart.push({id: p.id, name: p.name, price: p.price, currency: p.currency, icon: p.icon});
    renderShopper();
}

function removeFromCart(idx) { state.cart.splice(idx, 1); renderShopper(); }

function renderCart(el) {
    var h = '<div class="shop-nav"><h3>Shopping Cart</h3><button class="btn btn-sm btn-secondary" onclick="state.shopView=\'catalog\';renderShopper()">Continue Shopping</button></div>';
    if (!state.cart.length) { h += '<p class="text-muted" style="padding:2rem;text-align:center">Your cart is empty.</p>'; el.innerHTML = h; return; }
    var total = 0;
    h += '<div class="cart-container"><div class="cart-items">';
    state.cart.forEach(function(item, i) {
        total += item.price;
        h += '<div class="cart-item"><span class="cart-item-icon">' + item.icon + '</span>';
        h += '<div class="cart-item-info"><div class="cart-item-name">' + esc(item.name) + '</div><div class="cart-item-price">' + fmt(item.price, item.currency) + '</div></div>';
        h += '<button class="cart-item-remove" onclick="removeFromCart(' + i + ')">x</button></div>';
    });
    h += '</div><div class="cart-footer"><div class="cart-total"><span>Total</span><span>' + fmt(total) + '</span></div>';
    h += '<div class="cart-actions"><button class="btn btn-primary" onclick="state.shopView=\'customer_details\';renderShopper()">Proceed to Checkout</button><button class="btn btn-secondary" onclick="state.cart=[];renderShopper()">Clear</button></div></div></div>';
    el.innerHTML = h;
}

function renderCustomerDetails(el) {
    var total = 0; state.cart.forEach(function(i) { total += i.price; });
    var h = '<div class="shop-nav"><h3>Customer Details</h3><button class="btn btn-sm btn-secondary" onclick="state.shopView=\'cart\';renderShopper()">Back to Cart</button></div>';
    h += '<div class="checkout-form-panel">';
    h += '<div class="checkout-section"><label>Full Name <span class="required">*</span></label><input type="text" id="cd-name" placeholder="John Doe" value="' + esc(state.checkoutDetails.name || '') + '"></div>';
    h += '<div class="checkout-section"><label>Email Address <span class="required">*</span></label><input type="email" id="cd-email" placeholder="john@example.com" value="' + esc(state.checkoutDetails.email || '') + '"></div>';
    h += '<div class="checkout-section"><label>Street Address <span class="required">*</span></label><input type="text" id="cd-address" placeholder="123 Main Street" value="' + esc(state.checkoutDetails.address || '') + '"></div>';
    h += '<div style="display:flex;gap:.5rem">';
    h += '<div class="checkout-section" style="flex:1"><label>City <span class="required">*</span></label><input type="text" id="cd-city" placeholder="Zurich" value="' + esc(state.checkoutDetails.city || '') + '"></div>';
    h += '<div class="checkout-section" style="flex:1"><label>Postal Code</label><input type="text" id="cd-zip" placeholder="8001" value="' + esc(state.checkoutDetails.zip || '') + '"></div>';
    h += '</div>';
    h += '<div style="display:flex;gap:.5rem">';
    h += '<div class="checkout-section" style="flex:1"><label>Country</label><input type="text" id="cd-country" placeholder="Switzerland" value="' + esc(state.checkoutDetails.country || '') + '"></div>';
    h += '<div class="checkout-section" style="flex:1"><label>Phone</label><input type="text" id="cd-phone" placeholder="+41 79 123 4567" value="' + esc(state.checkoutDetails.phone || '') + '"></div>';
    h += '</div>';
    h += '<p style="font-size:.72rem;color:var(--text-muted);margin-top:.25rem">* Required fields</p>';
    h += '<div style="margin-top:1rem"><button class="btn btn-primary" onclick="proceedToPayment()" style="width:100%">Continue to Payment (' + fmt(total) + ')</button></div>';
    h += '</div>';
    el.innerHTML = h;
}

function proceedToPayment() {
    var name = ($('cd-name') || {}).value || '';
    var email = ($('cd-email') || {}).value || '';
    var address = ($('cd-address') || {}).value || '';
    var city = ($('cd-city') || {}).value || '';
    if (!name.trim() || !email.trim() || !address.trim() || !city.trim()) {
        alert('Please fill in all required fields (name, email, address, city).');
        return;
    }
    state.checkoutDetails = { name: name, email: email, address: address, city: city, zip: ($('cd-zip') || {}).value || '', country: ($('cd-country') || {}).value || '', phone: ($('cd-phone') || {}).value || '' };
    state.shopView = 'checkout';
    renderShopper();
}

function renderCheckout(el) {
    var total = 0; state.cart.forEach(function(i) { total += i.price; });
    var h = '<div class="shop-nav"><h3>Payment</h3><button class="btn btn-sm btn-secondary" onclick="state.shopView=\'customer_details\';renderShopper()">Back to Details</button></div>';
    h += '<div class="checkout-summary"><strong>Customer:</strong> ' + esc(state.checkoutDetails.name) + ' &middot; ' + esc(state.checkoutDetails.email) + '</div>';
    h += '<div class="checkout-section"><label>Payment Flow</label><select id="checkout-flow">';
    h += '<option value="hostedcheckout">Hosted Checkout (recommended)</option>';
    h += '<option value="s2s">Server-to-Server (advanced)</option>';
    h += '</select><small>Hosted Checkout = Worldline-hosted payment page. S2S = direct API call (requires PCI compliance or tokenization).</small></div>';
    h += '<div style="margin-top:1rem"><button class="btn btn-primary" onclick="checkout()" style="width:100%">Pay ' + fmt(total) + '</button></div>';
    el.innerHTML = h;
}

async function checkout() {
    if (!state.configured) { alert('Please configure API credentials first.'); switchTab('config'); return; }
    if (!state.cart.length) return;

    var total = 0; state.cart.forEach(function(i) { total += i.price; });
    state.paymentFlow = ($('checkout-flow') || {}).value || 'hostedcheckout';
    state.shopView = 'processing'; renderShopper();

    var cd = state.checkoutDetails;
    var parts = (cd.name || '').split(' ');
    var body = { amount: total, currency: 'EUR', items: state.cart, payer: { FirstName: parts[0] || '', LastName: parts.slice(1).join(' ') || '', Email: cd.email || '' } };

    try {
        var url = state.paymentFlow === 'hostedcheckout' ? '/api/hosted-checkout/create' : '/api/payment/create';
        var r = await api(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        if (r.data.log) addApiLog(r.data.log);

        if (r.ok && r.data.success) {
            state.currentOrderId = r.data.order_id;
            if (state.paymentFlow === 'hostedcheckout') {
                state.paymentToken = r.data.hc_id;
                if (r.data.redirect_url) {
                    var popup = window.open(r.data.redirect_url, 'wlop_payment', 'width=600,height=700,scrollbars=yes');
                    waitForReturn(popup);
                }
            } else {
                state.currentPaymentId = r.data.payment_id;
                if (r.data.redirect_url) {
                    var popup = window.open(r.data.redirect_url, 'wlop_payment', 'width=600,height=700,scrollbars=yes');
                    waitForReturn(popup);
                } else {
                    // No redirect needed - check status directly
                    await doStatusCheck();
                }
            }
        } else {
            state.shopView = 'result';
            state.paymentResult = {success: false, error: r.data.error || 'Payment initialization failed'};
            renderShopper();
        }
    } catch(e) {
        state.shopView = 'result';
        state.paymentResult = {success: false, error: e.message};
        renderShopper();
    }
}

function waitForReturn(popup) {
    // Listen for postMessage from popup
    window.addEventListener('message', function handler(ev) {
        if (ev.data && ev.data.type === 'wlop_return') {
            window.removeEventListener('message', handler);
            addApiLog({id: _uid(), timestamp: new Date().toISOString(), step: 'Redirect', endpoint: 'Customer returned from Worldline', method: '-', status_code: '-', explanation: 'Customer completed the payment page and returned to the shop.', order_id: state.currentOrderId});
            if (ev.data.status === 'fail') {
                state.shopView = 'result';
                state.paymentResult = {success: false, error: 'Payment cancelled by customer'};
                renderShopper();
            } else {
                doStatusCheck();
            }
        }
    });
    // Fallback: poll for popup close
    var poll = setInterval(function() {
        if (popup && popup.closed) { clearInterval(poll); doStatusCheck(); }
    }, 1000);
}

async function doStatusCheck() {
    try {
        var r;
        if (state.paymentFlow === 'hostedcheckout') {
            r = await api('/api/hosted-checkout/status', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({hc_id: state.paymentToken})});
        } else {
            r = await api('/api/payment/status', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({payment_id: state.currentPaymentId})});
        }
        if (r.data.log) addApiLog(r.data.log);

        if (r.ok && r.data.success) {
            var sc = r.data.status_code;
            var success = (sc === 5 || sc === 9); // 5=Authorised, 9=Captured
            state.paymentResult = {
                success: success,
                status: r.data.status,
                status_code: sc,
                payment_id: r.data.payment_id || state.currentPaymentId,
                data: r.data.data,
                captured: sc === 9,
            };
            state.currentPaymentId = r.data.payment_id || state.currentPaymentId;
        } else {
            state.paymentResult = {success: false, error: r.data.error || 'Status check failed'};
        }
    } catch(e) {
        state.paymentResult = {success: false, error: e.message};
    }
    state.shopView = 'result';
    state.cart = [];
    renderShopper();
}

function renderResult(el) {
    var res = state.paymentResult || {};
    var h = '<div class="result-view">';
    if (res.success) {
        h += '<div class="result-icon success">&#10003;</div>';
        h += '<h3>Payment ' + esc(res.status || 'Successful') + '!</h3>';
        h += '<div class="result-details">';
        h += '<div class="result-detail-row"><span>Order</span><span>' + esc(state.currentOrderId || '-') + '</span></div>';
        h += '<div class="result-detail-row"><span>Status</span><span>' + esc(res.status) + ' (' + res.status_code + ')</span></div>';
        if (res.payment_id) h += '<div class="result-detail-row"><span>Payment ID</span><span style="font-size:.72rem">' + esc(res.payment_id) + '</span></div>';
        h += '</div>';
        if (res.status_code === 5 && !res.captured) {
            h += '<button class="btn btn-success" onclick="capturePayment()">Capture Payment</button> ';
        }
        if (res.captured) h += '<p class="text-muted" style="margin-top:.5rem">Payment captured and settled.</p>';
    } else {
        h += '<div class="result-icon fail">&#10007;</div>';
        h += '<h3>Payment Failed</h3>';
        h += '<p class="text-muted">' + esc(typeof res.error === 'string' ? res.error : JSON.stringify(res.error)) + '</p>';
    }
    h += '<button class="btn btn-secondary" style="margin-top:1rem" onclick="state.shopView=\'catalog\';state.paymentResult=null;state.paymentToken=null;state.currentPaymentId=null;state.currentOrderId=null;state.checkoutDetails={name:\'\',email:\'\',address:\'\',city:\'\',zip:\'\',country:\'\',phone:\'\'};renderShopper()">New Order</button>';
    h += '</div>';
    el.innerHTML = h;
}

async function capturePayment() {
    var res = state.paymentResult;
    if (!res || !res.payment_id) return;
    try {
        var txnKey = state.paymentToken || res.payment_id;
        var r = await api('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({payment_id: res.payment_id, txn_key: txnKey, amount: null})});
        if (r.data.log) addApiLog(r.data.log);
        if (r.ok) { state.paymentResult.captured = true; state.paymentResult.status = 'Captured / Paid'; state.paymentResult.status_code = 9; }
        renderShopper();
    } catch(e) {}
}

function _uid() { return Math.random().toString(36).substr(2, 12); }

// ================ DEVELOPER PANEL ================
function addApiLog(log) {
    state.apiLogs.unshift(log);
    renderDevPanel();
}

function renderDevPanel() {
    var el = $('developer-content');
    if (!state.apiLogs.length) {
        el.innerHTML = '<div class="dev-empty-state"><div class="dev-empty-icon">&lt;/&gt;</div><p>API calls will appear here.</p><p class="dev-hint">Start by adding items to the cart and checking out.</p></div>';
        return;
    }
    var h = '';
    state.apiLogs.forEach(function(log) {
        var step = (log.step || '').toLowerCase();
        var badgeClass = step.indexOf('create') >= 0 ? 'badge-pp' : (step.indexOf('status') >= 0 || step.indexOf('details') >= 0 ? 'badge-txn' : (step === 'redirect' ? 'badge-redirect' : (step.indexOf('capture') >= 0 ? 'badge-capture' : 'badge-pp')));
        var statusClass = log.status_code === 200 || log.status_code === 201 ? 's-ok' : (log.status_code === '-' ? '' : 's-err');
        h += '<div class="api-entry" onclick="this.classList.toggle(\'open\')">';
        h += '<div class="api-entry-header">';
        h += '<span class="api-step-badge ' + badgeClass + '">' + esc(log.step) + '</span>';
        h += '<span class="api-entry-method">' + esc(log.method || 'POST') + '</span>';
        h += '<span class="api-entry-endpoint">' + esc(log.endpoint) + '</span>';
        if (log.status_code && log.status_code !== '-') h += '<span class="api-entry-status ' + statusClass + '">' + log.status_code + '</span>';
        h += '<span class="api-entry-time">' + (log.timestamp ? fmtTime(log.timestamp) : '') + '</span>';
        h += '<span class="api-entry-toggle">&#9654;</span>';
        h += '</div>';
        h += '<div class="api-entry-body">';
        if (log.explanation) h += '<div class="api-explanation">' + esc(log.explanation) + '</div>';
        if (log.request) h += '<div class="api-section"><div class="api-section-label">Request</div><div class="api-json">' + syntaxHL(log.request) + '</div></div>';
        if (log.response) h += '<div class="api-section"><div class="api-section-label">Response</div><div class="api-json">' + syntaxHL(log.response) + '</div></div>';
        h += '</div></div>';
    });
    el.innerHTML = h;
}

function clearLogs() { api('/api/logs/clear', {method:'POST'}); state.apiLogs = []; renderDevPanel(); }

// ================ PRODUCTS VIEW ================
async function loadProducts() {
    try { var r = await api('/api/products'); state.products = r.data; renderProductGrid(); } catch(e) {}
}

function renderProductGrid() {
    var el = $('products-grid'); if (!el) return;
    var h = '';
    state.products.forEach(function(p) {
        h += '<div class="product-card ' + (p.active ? '' : 'inactive') + '">';
        h += '<div class="product-actions"><button title="Edit" onclick="editProduct(\'' + p.id + '\')">&#9998;</button><button title="Delete" onclick="deleteProduct(\'' + p.id + '\')">&#10007;</button></div>';
        h += '<div class="product-icon">' + p.icon + '</div>';
        h += '<div class="product-name">' + esc(p.name) + '</div>';
        h += '<div class="product-desc">' + esc(p.description) + '</div>';
        h += '<div class="product-price">' + fmt(p.price, p.currency) + '</div>';
        h += '</div>';
    });
    el.innerHTML = h || '<p class="text-muted text-center" style="padding:2rem">No products yet.</p>';
}

function showAddProduct() { $('product-form-card').classList.remove('hidden'); $('product-form-title').textContent = 'Add Product'; $('pf-submit-btn').textContent = 'Add Product'; $('product-form').reset(); $('pf-id').value = ''; loadIconPicker(); }
function hideProductForm() { $('product-form-card').classList.add('hidden'); }
function editProduct(pid) {
    var p = state.products.find(function(x) { return x.id === pid; });
    if (!p) return;
    $('product-form-card').classList.remove('hidden');
    $('product-form-title').textContent = 'Edit Product';
    $('pf-submit-btn').textContent = 'Save Changes';
    $('pf-id').value = p.id; $('pf-name').value = p.name; $('pf-desc').value = p.description || '';
    $('pf-price').value = (p.price / 100).toFixed(2);
    loadIconPicker(p.icon);
}
async function deleteProduct(pid) { await api('/api/products/' + pid, {method:'DELETE'}); await loadProducts(); }
async function saveProduct(ev) {
    ev.preventDefault();
    var body = { name: $('pf-name').value, description: $('pf-desc').value, price: Math.round(parseFloat($('pf-price').value) * 100), icon: (document.querySelector('.icon-option.selected') || {}).dataset.icon || '\U0001F4E6', active: true };
    if ($('pf-id').value) body.id = $('pf-id').value;
    await api('/api/products', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    hideProductForm(); await loadProducts();
}
function loadIconPicker(sel) {
    api('/api/icons').then(function(r) {
        var h = '';
        (r.data || []).forEach(function(ic) { h += '<div class="icon-option ' + (ic === sel ? 'selected' : '') + '" data-icon="' + ic + '" onclick="document.querySelectorAll(\'.icon-option\').forEach(function(e){e.classList.remove(\'selected\')});this.classList.add(\'selected\')">' + ic + '</div>'; });
        $('icon-picker').innerHTML = h;
    });
}

// ================ ORDERS VIEW ================
async function refreshOrders() {
    try {
        var r = await api('/api/transactions');
        renderOrderStats(r.data);
        renderOrderTable(r.data);
    } catch(e) {}
}

function renderOrderStats(txns) {
    var total = txns.length, rev = 0, auth = 0, cap = 0;
    txns.forEach(function(t) { rev += t.amount || 0; if (t.status_code === 5) auth++; if (t.status_code === 9) cap++; });
    $('stat-total').textContent = total;
    $('stat-revenue').textContent = fmt(rev);
    $('stat-authorized').textContent = auth;
    $('stat-captured').textContent = cap;
}

function renderOrderTable(txns) {
    var tb = $('txn-table-body');
    if (!txns.length) { tb.innerHTML = '<tr class="empty-row"><td colspan="8">No transactions yet.</td></tr>'; return; }
    var h = '';
    txns.forEach(function(t) {
        var sc = 'status-' + (t.status_code === 5 ? 'authorized' : (t.status_code === 9 ? 'captured' : (t.status_code === 2 || t.status_code === 75 || t.status_code === 96 ? 'failed' : 'initialized')));
        var pm = '';
        if (t.payment_means) {
            pm = (t.payment_means.Brand || '') + ' ' + (t.payment_means.DisplayText || '');
        }
        var flowTag = t.payment_flow === 'ServerToServer' ? '<span class="flow-tag txn">S2S</span>' : '<span class="flow-tag pp">HC</span>';
        h += '<tr>';
        h += '<td><strong>' + esc(t.order_id || '-') + '</strong>';
        if (t.description) h += '<div class="order-desc-hint">' + esc(t.description) + '</div>';
        h += '</td>';
        h += '<td>' + esc(t.customer_name || 'Guest') + '</td>';
        h += '<td>' + fmt(t.amount || 0, t.currency) + '</td>';
        h += '<td><span class="status-badge ' + sc + '">' + esc(t.status || '?') + '</span></td>';
        h += '<td>' + flowTag + '</td>';
        h += '<td>' + esc(pm || '-') + '</td>';
        h += '<td>' + (t.created ? fmtTime(t.created) : '-') + '</td>';
        h += '<td style="white-space:nowrap">';
        if (t.status_code === 5 && t.payment_id) h += '<button class="btn btn-sm btn-success" onclick="captureMerchant(\'' + esc(t.payment_id) + '\',\'' + esc(t.hc_id || t.payment_id) + '\',' + (t.amount || 0) + ')">Capture</button> ';
        else if (t.status_code === 9) h += '<span class="text-muted">Settled</span> ';
        if (t.order_id) h += '<button class="btn btn-sm btn-secondary" onclick="showOrderJourney(\'' + esc(t.order_id) + '\')">Journey</button>';
        h += '</td></tr>';
    });
    tb.innerHTML = h;
}

async function captureMerchant(paymentId, txnKey, amount) {
    try {
        var r = await api('/api/capture', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({payment_id: paymentId, txn_key: txnKey, amount: amount})});
        if (r.data.log) addApiLog(r.data.log);
        refreshOrders();
        if (state.paymentResult && state.currentPaymentId === paymentId) { state.paymentResult.captured = true; state.paymentResult.status_code = 9; renderShopper(); }
    } catch(e) {}
}

// ================ ORDER JOURNEY ================
async function showOrderJourney(orderId) {
    var overlay = $('order-journey-overlay');
    overlay.classList.remove('hidden');
    overlay.innerHTML = '<div class="journey-panel"><div class="processing-view"><div class="processing-spinner"></div><p>Loading journey...</p></div></div>';
    try {
        var r = await api('/api/orders/' + encodeURIComponent(orderId) + '/journey');
        if (r.ok) renderJourneyPanel(r.data);
        else overlay.innerHTML = '<div class="journey-panel"><p class="text-muted" style="padding:2rem">Could not load journey.</p><button class="btn btn-secondary" onclick="closeJourney()">Close</button></div>';
    } catch(e) {
        overlay.innerHTML = '<div class="journey-panel"><p class="text-muted" style="padding:2rem">Error: ' + esc(e.message) + '</p><button class="btn btn-secondary" onclick="closeJourney()">Close</button></div>';
    }
}

function renderJourneyPanel(data) {
    var h = '<div class="journey-panel">';
    h += '<div class="journey-header"><h3>Order Journey: ' + esc(data.order_id) + '</h3>';
    h += '<button class="btn btn-sm btn-secondary" onclick="closeJourney()">Close</button></div>';
    h += '<div class="journey-summary">';
    h += '<span>Flow: <strong>' + esc(data.flow) + '</strong></span>';
    h += '<span>Amount: <strong>' + fmt(data.amount, data.currency) + '</strong></span>';
    h += '<span>Status: <span class="status-badge">' + esc(data.status) + '</span></span>';
    if (data.description) h += '<span>Desc: <strong>' + esc(data.description) + '</strong></span>';
    h += '</div>';
    h += '<div class="journey-timeline">';
    data.steps.forEach(function(step, idx) {
        var completedClass = step.completed ? 'step-done' : 'step-pending';
        h += '<div class="journey-step ' + completedClass + '">';
        h += '<div class="journey-step-marker"><div class="journey-dot"></div>';
        if (idx < data.steps.length - 1) h += '<div class="journey-connector"></div>';
        h += '</div>';
        h += '<div class="journey-step-content">';
        h += '<div class="journey-step-header">';
        h += '<span class="journey-step-name">' + esc(step.step) + '</span>';
        h += '<span class="journey-actor-badge badge-' + step.actor + '">' + esc(step.actor) + '</span>';
        if (step.optional) h += '<span class="journey-optional">optional</span>';
        if (step.timestamp) h += '<span class="journey-step-time">' + fmtTime(step.timestamp) + '</span>';
        if (step.status_code) h += '<span class="api-entry-status ' + (step.status_code === 200 || step.status_code === 201 ? 's-ok' : 's-err') + '">' + step.status_code + '</span>';
        h += '</div>';
        h += '<div class="journey-step-desc">' + esc(step.description) + '</div>';
        if (step.code_ref) h += '<div class="journey-code-ref">Code: <code>' + esc(step.code_ref) + '</code></div>';
        if (step.log_id) {
            var log = data.logs.find(function(l) { return l.id === step.log_id; });
            if (log) {
                h += '<details class="journey-log-detail"><summary>View API Request / Response</summary>';
                if (log.request) h += '<div class="api-section"><div class="api-section-label">Request</div><div class="api-json">' + syntaxHL(log.request) + '</div></div>';
                if (log.response) h += '<div class="api-section"><div class="api-section-label">Response</div><div class="api-json">' + syntaxHL(log.response) + '</div></div>';
                h += '</details>';
            }
        }
        h += '</div></div>';
    });
    h += '</div></div>';
    $('order-journey-overlay').innerHTML = h;
}

function closeJourney() { $('order-journey-overlay').classList.add('hidden'); }

// ================ FEATURE AUDIT ================
async function showFeatureAudit() {
    var panel = $('feature-audit-panel'), mainView = $('orders-main-view');
    if (!panel.classList.contains('hidden')) { panel.classList.add('hidden'); mainView.classList.remove('hidden'); return; }
    mainView.classList.add('hidden');
    panel.classList.remove('hidden');
    $('feature-audit-content').innerHTML = '<div class="processing-view"><div class="processing-spinner"></div><p>Loading audit...</p></div>';
    try {
        var r = await api('/api/feature-audit');
        if (r.ok) renderFeatureAudit(r.data);
    } catch(e) { $('feature-audit-content').innerHTML = '<p class="text-muted" style="padding:2rem">Error loading audit.</p>'; }
}

function renderFeatureAudit(data) {
    var s = data.stats;
    var h = '<div class="audit-container">';
    h += '<div class="audit-score-card">';
    h += '<div class="audit-score-circle"><svg viewBox="0 0 36 36"><path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="var(--border)" stroke-width="3"/>';
    h += '<path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="var(--primary)" stroke-width="3" stroke-dasharray="' + s.coverage_pct + ', 100"/></svg>';
    h += '<span class="score-text">' + s.coverage_pct + '%</span></div>';
    h += '<div class="audit-score-info"><h3>Worldline Direct Feature Coverage</h3>';
    h += '<p>' + s.implemented + ' of ' + s.total + ' API capabilities implemented in this demo</p></div></div>';
    data.categories.forEach(function(cat) {
        h += '<div class="audit-category card">';
        h += '<h4 class="audit-cat-title">' + esc(cat.name) + '</h4>';
        cat.features.forEach(function(f) {
            h += '<div class="audit-feature ' + (f.implemented ? 'implemented' : 'not-implemented') + '">';
            h += '<span class="audit-check">' + (f.implemented ? '&#10003;' : '&#9675;') + '</span>';
            h += '<div class="audit-feature-info"><strong>' + esc(f.name) + '</strong>';
            h += '<div class="audit-feature-desc">' + esc(f.description) + '</div>';
            if (f.endpoint) h += '<code class="audit-endpoint">' + esc(f.endpoint) + '</code>';
            h += '</div></div>';
        });
        h += '</div>';
    });
    h += '</div>';
    $('feature-audit-content').innerHTML = h;
}

function backToOrders() { $('feature-audit-panel').classList.add('hidden'); $('orders-main-view').classList.remove('hidden'); }

// ================ CUSTOMERS VIEW ================
async function loadCustomers(silent) {
    try { var r = await api('/api/customers'); state.customers = r.data; if (!silent) renderCustomerList(); } catch(e) {}
}

function renderCustomerList() {
    var el = $('customers-grid'); if (!el) return;
    var q = ($('customer-search') || {}).value || '';
    var filtered = state.customers.filter(function(c) {
        if (!q) return true;
        var ql = q.toLowerCase();
        return (c.name || '').toLowerCase().indexOf(ql) >= 0 || (c.email || '').toLowerCase().indexOf(ql) >= 0 || (c.company || '').toLowerCase().indexOf(ql) >= 0;
    });
    var h = '';
    filtered.forEach(function(c) {
        h += '<div class="customer-card" onclick="showCustomerDetail(\'' + c.id + '\')">';
        h += '<div class="customer-card-name">' + esc(c.name) + '</div>';
        h += '<div class="customer-card-company">' + esc(c.company || '-') + '</div>';
        h += '<div class="customer-card-meta"><span>' + esc(c.email || '-') + '</span><span><strong>' + (c.order_count || 0) + '</strong> orders</span><span><strong>' + fmt(c.total_spent || 0) + '</strong></span></div>';
        h += '</div>';
    });
    el.innerHTML = h || '<p class="text-muted text-center" style="padding:2rem">No customers yet.</p>';
    $('customer-list-view').classList.remove('hidden');
    $('customer-detail-view').classList.add('hidden');
}

function showAddCustomer() { $('customer-form-card').classList.remove('hidden'); $('customer-form-title').textContent = 'Add Customer'; $('cf-submit-btn').textContent = 'Add Customer'; $('customer-form').reset(); $('cf-id').value = ''; }
function hideCustomerForm() { $('customer-form-card').classList.add('hidden'); }
function editCustomer(cid) {
    var c = state.customers.find(function(x) { return x.id === cid; });
    if (!c) return;
    $('customer-form-card').classList.remove('hidden');
    $('customer-form-title').textContent = 'Edit Customer';
    $('cf-submit-btn').textContent = 'Save Changes';
    $('cf-id').value = c.id; $('cf-name').value = c.name; $('cf-email').value = c.email || '';
    $('cf-company').value = c.company || ''; $('cf-phone').value = c.phone || ''; $('cf-address').value = c.address || '';
}
async function saveCustomer(ev) {
    ev.preventDefault();
    var body = { name: $('cf-name').value, email: $('cf-email').value, company: $('cf-company').value, phone: $('cf-phone').value, address: $('cf-address').value };
    if ($('cf-id').value) body.id = $('cf-id').value;
    await api('/api/customers', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    hideCustomerForm(); await loadCustomers();
}
async function deleteCustomer(cid) { await api('/api/customers/' + cid, {method:'DELETE'}); await loadCustomers(); }
function backToCustomerList() { state.customerDetailId = null; renderCustomerList(); }

async function showCustomerDetail(cid) {
    state.customerDetailId = cid;
    $('customer-list-view').classList.add('hidden');
    $('customer-detail-view').classList.remove('hidden');
    var c = state.customers.find(function(x) { return x.id === cid; });
    if (!c) return;
    var ordersR = await api('/api/customers/' + cid + '/orders');
    var orders = ordersR.data || [];
    var h = '<div class="customer-detail">';
    h += '<div class="customer-info-card"><h3>' + esc(c.name) + '</h3>';
    h += '<div class="info-row"><span>Email</span><span>' + esc(c.email || '-') + '</span></div>';
    h += '<div class="info-row"><span>Company</span><span>' + esc(c.company || '-') + '</span></div>';
    h += '<div class="info-row"><span>Phone</span><span>' + esc(c.phone || '-') + '</span></div>';
    h += '<div class="info-row"><span>Address</span><span>' + esc(c.address || '-') + '</span></div>';
    h += '<div class="info-row"><span>Orders</span><span>' + orders.length + '</span></div>';
    var total = 0; orders.forEach(function(o) { if (o.status_code === 5 || o.status_code === 9) total += o.amount || 0; });
    h += '<div class="info-row"><span>Lifetime Value</span><span>' + fmt(total) + '</span></div>';
    h += '<div style="margin-top:.75rem;display:flex;gap:.4rem"><button class="btn btn-sm btn-secondary" onclick="editCustomer(\'' + cid + '\')">Edit</button><button class="btn btn-sm btn-danger" onclick="deleteCustomer(\'' + cid + '\');backToCustomerList()">Delete</button></div>';
    h += '</div>';
    h += '<div class="customer-info-card"><h3>Notes</h3>';
    h += '<div class="notes-list">';
    (c.notes || []).forEach(function(n) { h += '<div class="note-item">' + esc(n.text) + '<div class="note-time">' + fmtTime(n.timestamp) + '</div></div>'; });
    if (!(c.notes || []).length) h += '<p class="text-muted" style="font-size:.82rem">No notes yet.</p>';
    h += '</div>';
    h += '<div class="note-input-row"><input type="text" id="note-input" placeholder="Add a note..." onkeydown="if(event.key===\'Enter\')addNote(\'' + cid + '\')"><button class="btn btn-sm btn-primary" onclick="addNote(\'' + cid + '\')">Add</button></div>';
    h += '</div></div>';
    $('customer-detail-content').innerHTML = h;
}

async function addNote(cid) {
    var input = $('note-input');
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    await api('/api/customers/' + cid + '/notes', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:text})});
    await loadCustomers(true);
    showCustomerDetail(cid);
}

// ================ CONFIG ================
async function checkConfig() {
    try {
        var r = await api('/api/config/status');
        state.configured = r.data.configured;
        updateConfigUI(r.data);
        if (r.data.configured) {
            $('cfg-merchant-id').value = r.data.merchant_id || '';
            if (r.data.base_url) $('cfg-base-url').value = r.data.base_url;
            if (r.data.order_id_prefix) $('cfg-order-prefix').value = r.data.order_id_prefix;
            if (r.data.order_id_pattern) $('cfg-order-pattern').value = r.data.order_id_pattern;
            if (r.data.default_description) $('cfg-order-desc').value = r.data.default_description;
        }
    } catch(e) { state.configured = false; }
}

function updateConfigUI(d) {
    var banner = $('config-banner'), badge = $('config-status-badge');
    if (d && d.configured) {
        banner.classList.add('hidden'); badge.className = 'header-status connected'; badge.textContent = 'Connected';
        document.querySelectorAll('.tab-content').forEach(function(e) { e.classList.remove('has-banner'); });
    } else {
        banner.classList.remove('hidden'); badge.className = 'header-status disconnected'; badge.textContent = 'Not configured';
        document.querySelectorAll('.tab-content').forEach(function(e) { e.classList.add('has-banner'); });
    }
}

async function saveConfig(ev) {
    ev.preventDefault();
    var msg = $('config-message'); msg.textContent = '';
    var body = { merchant_id: $('cfg-merchant-id').value, api_key: $('cfg-api-key').value, api_secret: $('cfg-api-secret').value, base_url: $('cfg-base-url').value, order_id_prefix: $('cfg-order-prefix').value, order_id_pattern: $('cfg-order-pattern').value, default_description: $('cfg-order-desc').value };
    try {
        var r = await api('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        if (r.ok) { state.configured = true; updateConfigUI({configured:true}); msg.className = 'form-message success'; msg.textContent = 'Saved!'; setTimeout(function(){switchTab('explorer');}, 600); }
        else { msg.className = 'form-message error'; msg.textContent = r.data.error || 'Failed'; }
    } catch(e) { msg.className = 'form-message error'; msg.textContent = 'Network error'; }
}

// ================ SPLIT HANDLE ================
(function(){
    var handle = $('split-handle'); if (!handle) return;
    var sv = handle.parentElement, dragging = false;
    handle.addEventListener('mousedown', function(e) { dragging = true; e.preventDefault(); document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none'; });
    document.addEventListener('mousemove', function(e) { if (!dragging) return; var r = sv.getBoundingClientRect(); var pct = Math.max(25, Math.min(75, ((e.clientX - r.left) / r.width) * 100)); sv.querySelector('.shopper-panel').style.cssText = 'flex:none;width:'+pct+'%'; sv.querySelector('.developer-panel').style.cssText = 'flex:none;width:'+(100-pct)+'%'; });
    document.addEventListener('mouseup', function() { if (dragging) { dragging = false; document.body.style.cursor = ''; document.body.style.userSelect = ''; } });
})();

// ================ CODE VIEWER ================
var codeState = {
    currentFile: null,
    content: '',
    annotations: {},
    unlocked: false,
};

async function loadCode(filename, btn) {
    if (btn) { document.querySelectorAll('.code-file-btn').forEach(function(b) { b.classList.remove('active'); }); btn.classList.add('active'); }
    try {
        var r = await api('/api/code/' + filename);
        if (r.ok) {
            codeState.currentFile = filename;
            codeState.content = r.data.content;
            codeState.annotations = r.data.annotations || {};
            $('code-filename').textContent = r.data.filename;
            $('code-lang').textContent = r.data.language;
            renderCodeView();
        }
    } catch(e) {}
}

function renderCodeView() {
    var el = $('code-content');
    if (codeState.unlocked) {
        el.innerHTML = '<textarea id="code-editor">' + esc(codeState.content) + '</textarea>';
        $('code-save-btn').classList.remove('hidden');
        return;
    }
    $('code-save-btn').classList.add('hidden');
    var lines = codeState.content.split('\n');
    var h = '<table class="code-table"><tbody>';
    lines.forEach(function(line, idx) {
        var lineNum = idx + 1;
        var lineStr = String(lineNum);
        var ann = codeState.annotations[lineStr];
        var lineLC = line.toLowerCase();
        var isRoute = lineLC.indexOf('@app.route') >= 0 || lineLC.indexOf('def ') >= 0 && lineLC.indexOf('(') >= 0;
        var isApi = lineLC.indexOf('wlop_request') >= 0 || lineLC.indexOf('hostedcheckout') >= 0 || lineLC.indexOf('payment') >= 0 && lineLC.indexOf('/v2/') >= 0;
        var cls = ann ? 'annotated' : '';
        if (isRoute) cls += ' route';
        if (isApi) cls += ' saferpay';
        h += '<tr class="code-row ' + cls + '" onclick="toggleAnnotation(' + lineNum + ')">';
        h += '<td class="code-ln">' + lineNum + '</td>';
        h += '<td class="code-line">' + esc(line || ' ') + '</td></tr>';
        if (ann) {
            h += '<tr class="annotation-row" id="ann-' + lineNum + '">';
            h += '<td class="code-annotation" colspan="2"><strong>Line ' + lineNum + ':</strong> ' + esc(ann) + '</td></tr>';
        }
    });
    h += '</tbody></table>';
    el.innerHTML = h;
}

function toggleAnnotation(lineNum) {
    var row = $('ann-' + lineNum);
    if (row) row.classList.toggle('visible');
}

function showUnlockPrompt() { $('unlock-prompt').classList.remove('hidden'); }
async function unlockCode() {
    var pw = $('unlock-password').value;
    var msg = $('unlock-message');
    try {
        var r = await api('/api/code/unlock', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({password: pw})});
        if (r.ok && r.data.unlocked) {
            codeState.unlocked = true;
            $('unlock-prompt').classList.add('hidden');
            $('lock-badge').textContent = 'Editing'; $('lock-badge').className = 'lock-badge unlocked';
            renderCodeView();
        } else { msg.className = 'form-message error'; msg.textContent = 'Wrong password'; }
    } catch(e) { msg.className = 'form-message error'; msg.textContent = 'Error'; }
}

async function saveCode() {
    var editor = $('code-editor'); if (!editor) return;
    var pw = prompt('Enter service password to save:');
    if (!pw) return;
    try {
        var r = await api('/api/code/' + codeState.currentFile, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({content: editor.value, password: pw})});
        if (r.ok) { alert('Saved!'); codeState.content = editor.value; }
        else alert(r.data.error || 'Save failed');
    } catch(e) { alert('Error saving'); }
}

// ================ INIT ================
checkConfig();
loadProducts().then(function() { renderShopper(); });
loadCustomers(true);

})();
