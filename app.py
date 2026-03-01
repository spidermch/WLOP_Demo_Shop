import os
import uuid
import hmac
import hashlib
import base64
import requests as http_requests
from datetime import datetime, timezone
from email.utils import formatdate
from flask import Flask, render_template, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'wlop-explorer-dev-key-change-me')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

STORE = {}

DEFAULT_PRODUCTS = [
    {'id': 'prod_001', 'name': 'Swiss Luxury Watch', 'description': 'Elegant timepiece crafted in Switzerland', 'price': 29900, 'currency': 'EUR', 'icon': '\u231A', 'active': True},
    {'id': 'prod_002', 'name': 'Premium Chocolate Box', 'description': 'Assorted Swiss chocolate collection', 'price': 4990, 'currency': 'EUR', 'icon': '\U0001F36B', 'active': True},
    {'id': 'prod_003', 'name': 'Swiss Army Knife', 'description': 'Multi-tool classic red design', 'price': 8900, 'currency': 'EUR', 'icon': '\U0001F527', 'active': True},
    {'id': 'prod_004', 'name': 'Fondue Set Deluxe', 'description': 'Traditional ceramic fondue set for 4', 'price': 12900, 'currency': 'EUR', 'icon': '\U0001FAD5', 'active': True},
]

ICONS = ['\u231A', '\U0001F36B', '\U0001F527', '\U0001FAD5', '\U0001F455', '\U0001F45F', '\U0001F4F1', '\U0001F4BB',
         '\U0001F3AE', '\U0001F4DA', '\U0001F3A7', '\u2615', '\U0001F377', '\U0001F48D', '\U0001F381',
         '\U0001FA91', '\U0001F5BC', '\U0001F9F8', '\U0001F392', '\U0001F460']


def _uid():
    return uuid.uuid4().hex[:12]


def get_store():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    sid = session['session_id']
    if sid not in STORE:
        STORE[sid] = {
            'transactions': {},
            'logs': [],
            'products': [p.copy() for p in DEFAULT_PRODUCTS],
            'customers': {},
            'product_seq': len(DEFAULT_PRODUCTS) + 1,
        }
    return STORE[sid]


def get_config():
    return session.get('config')


# ==================== WLOP API Helpers ====================

def wlop_sign(method, content_type, date_str, resource, api_secret):
    """Create HMAC-SHA256 signature for Worldline Direct API."""
    if method.upper() == 'POST':
        string_to_hash = f"{method.upper()}\n{content_type}\n{date_str}\n{resource}\n"
    else:
        string_to_hash = f"{method.upper()}\n{date_str}\n{resource}\n"
    sig = hmac.new(api_secret.encode('utf-8'), string_to_hash.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(sig).decode('utf-8')


def wlop_request(method, resource, config, payload=None):
    """Make an authenticated request to the Worldline Direct API."""
    base_url = config['base_url'].rstrip('/')
    url = f"{base_url}{resource}"
    content_type = 'application/json; charset=utf-8' if method.upper() == 'POST' else ''
    date_str = formatdate(timeval=None, localtime=False, usegmt=True)

    signature = wlop_sign(method.upper(), content_type, date_str, resource, config['api_secret'])
    auth_header = f"GCS v1HMAC:{config['api_key']}:{signature}"

    headers = {
        'Date': date_str,
        'Authorization': auth_header,
    }
    if method.upper() == 'POST':
        headers['Content-Type'] = content_type

    if method.upper() == 'POST':
        return http_requests.post(url, json=payload, headers=headers, timeout=30)
    else:
        return http_requests.get(url, headers=headers, timeout=30)


def generate_order_id(config, flow='HC'):
    prefix = config.get('order_id_prefix', 'WLOP')
    pattern = config.get('order_id_pattern', 'prefix-uuid')
    uid = uuid.uuid4().hex[:8].upper()
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    seq = str(int(datetime.utcnow().timestamp()))[-6:]
    if pattern == 'prefix-timestamp':
        return f"{prefix}-{ts}"
    elif pattern == 'prefix-seq':
        return f"{prefix}-{seq}"
    elif pattern == 'flow-prefix-uuid':
        tag = 'HC' if flow == 'HC' else 'S2S'
        return f"{tag}-{prefix}-{uid}"
    else:
        return f"{prefix}-{uid}"


def _make_log(step, endpoint, explanation, order_id=None):
    entry = {
        'id': _uid(),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'step': step,
        'endpoint': endpoint,
        'method': 'POST',
        'request': None,
        'response': None,
        'status_code': None,
        'explanation': explanation,
    }
    if order_id:
        entry['order_id'] = order_id
    return entry


# ==================== WLOP Status Codes ====================

WLOP_STATUS_CODES = {
    0: {'name': 'CREATED', 'label': 'Created', 'final': False},
    2: {'name': 'DECLINED', 'label': 'Declined', 'final': True},
    4: {'name': 'ORDER_STORED', 'label': 'Order Stored', 'final': False},
    5: {'name': 'AUTHORISED', 'label': 'Authorised', 'final': False},
    6: {'name': 'AUTH_CANCELLED', 'label': 'Auth Cancelled', 'final': True},
    7: {'name': 'DELETED', 'label': 'Payment Deleted', 'final': True},
    8: {'name': 'REFUNDED', 'label': 'Refunded', 'final': True},
    9: {'name': 'CAPTURED', 'label': 'Captured / Paid', 'final': True},
    46: {'name': 'WAITING_AUTH', 'label': 'Waiting Authentication', 'final': False},
    50: {'name': 'AUTH_WAITING_EXT', 'label': 'Waiting External', 'final': False},
    51: {'name': 'AUTH_WAITING', 'label': 'Auth Waiting', 'final': False},
    55: {'name': 'STANDBY', 'label': 'Standby', 'final': False},
    75: {'name': 'CANCELLED_CUSTOMER', 'label': 'Cancelled by Customer', 'final': True},
    81: {'name': 'REFUND_PENDING', 'label': 'Refund Pending', 'final': False},
    83: {'name': 'REFUND_REFUSED', 'label': 'Refund Refused', 'final': True},
    91: {'name': 'CAPTURE_PENDING', 'label': 'Capture Pending', 'final': False},
    93: {'name': 'CAPTURE_REFUSED', 'label': 'Capture Refused', 'final': True},
    96: {'name': 'CANCELLED', 'label': 'Cancelled', 'final': True},
    99: {'name': 'PROCESSING', 'label': 'Being Processed', 'final': False},
}


# ==================== Feature Audit ====================

WLOP_FEATURE_AUDIT = [
    {'name': 'Payment Initiation', 'features': [
        {'id': 'hc_create', 'name': 'Create Hosted Checkout', 'endpoint': 'POST /v2/{mid}/hostedcheckouts', 'implemented': True,
         'description': 'Create a Worldline-hosted payment page. All sensitive data handled by Worldline.'},
        {'id': 's2s_create', 'name': 'Create Payment (S2S)', 'endpoint': 'POST /v2/{mid}/payments', 'implemented': True,
         'description': 'Server-to-server payment creation for full control over the payment process.'},
    ]},
    {'name': 'Payment Status', 'features': [
        {'id': 'hc_status', 'name': 'Get Hosted Checkout Status', 'endpoint': 'GET /v2/{mid}/hostedcheckouts/{id}', 'implemented': True,
         'description': 'Retrieve the status and payment details of a hosted checkout session.'},
        {'id': 'pay_status', 'name': 'Get Payment Details', 'endpoint': 'GET /v2/{mid}/payments/{id}', 'implemented': True,
         'description': 'Get full details and current status of any payment.'},
    ]},
    {'name': 'Transaction Management', 'features': [
        {'id': 'capture', 'name': 'Capture Payment', 'endpoint': 'POST /v2/{mid}/payments/{id}/capture', 'implemented': True,
         'description': 'Capture an authorized payment to settle funds.'},
        {'id': 'cancel', 'name': 'Cancel Payment', 'endpoint': 'POST /v2/{mid}/payments/{id}/cancel', 'implemented': False,
         'description': 'Cancel an authorized payment before capture. Releases reserved funds.'},
        {'id': 'refund', 'name': 'Refund Payment', 'endpoint': 'POST /v2/{mid}/payments/{id}/refund', 'implemented': False,
         'description': 'Refund a captured payment (full or partial) back to the customer.'},
    ]},
    {'name': 'Tokenization', 'features': [
        {'id': 'htp', 'name': 'Hosted Tokenization Page', 'endpoint': 'POST /v2/{mid}/hostedtokenizations', 'implemented': False,
         'description': 'Embed tokenization iFrame in merchant page. Store card as token for future payments.'},
        {'id': 'token_create', 'name': 'Create Token', 'endpoint': 'POST /v2/{mid}/tokens', 'implemented': False,
         'description': 'Create a reusable payment token from a completed transaction.'},
        {'id': 'token_delete', 'name': 'Delete Token', 'endpoint': 'DELETE /v2/{mid}/tokens/{id}', 'implemented': False,
         'description': 'Remove a stored payment token from the vault.'},
    ]},
    {'name': 'Advanced Features', 'features': [
        {'id': 'paybylink', 'name': 'Pay-by-Link', 'endpoint': 'Merchant Portal', 'implemented': False,
         'description': 'Generate payment links to send via email or messaging for remote payments.'},
        {'id': 'recurring', 'name': 'Recurring Payments', 'endpoint': 'POST /v2/{mid}/payments (recurring)', 'implemented': False,
         'description': 'Process recurring/subscription payments using stored credentials.'},
        {'id': 'dcc', 'name': 'Dynamic Currency Conversion', 'endpoint': 'DCC via payment flow', 'implemented': False,
         'description': 'Allow cardholders to pay in their own currency with real-time conversion rates.'},
    ]},
    {'name': 'Risk & Security', 'features': [
        {'id': '3ds', 'name': '3-D Secure 2.x (automatic)', 'endpoint': None, 'implemented': True,
         'description': '3-D Secure authentication handled automatically by Worldline during payment flows.'},
        {'id': 'fraud', 'name': 'Fraud Detection', 'endpoint': None, 'implemented': False,
         'description': 'Advanced fraud screening with customizable rules and machine learning scoring.'},
    ]},
]


# ==================== Journey Templates ====================

JOURNEY_TEMPLATES = {
    'HostedCheckout': [
        {'step': 'Cart & Checkout', 'actor': 'merchant',
         'description': 'Customer selects products and clicks "Pay Now". The merchant app collects cart items, calculates total, and prepares the CreateHostedCheckout request.',
         'code_ref': 'app.js : checkout()', 'api_call': None},
        {'step': 'CreateHostedCheckout', 'actor': 'worldline',
         'description': 'Merchant server sends CreateHostedCheckout to Worldline with amount, currency, merchantReference, and returnUrl. Worldline creates a session and returns hostedCheckoutId + redirectUrl.',
         'code_ref': 'app.py : create_hosted_checkout()', 'api_call': 'hostedcheckouts'},
        {'step': 'Customer Redirect', 'actor': 'browser',
         'description': 'Customer is redirected to the Worldline-hosted payment page. Card data is entered on Worldline servers. PCI scope stays with Worldline - the merchant never sees raw card data.',
         'code_ref': 'app.js : window.open()', 'api_call': None},
        {'step': 'GetHostedCheckoutStatus', 'actor': 'worldline',
         'description': 'After customer returns, merchant calls GetHostedCheckoutStatus with the hostedCheckoutId. Worldline returns the payment status, payment ID, and transaction details.',
         'code_ref': 'app.py : get_hc_status()', 'api_call': 'hostedcheckouts/'},
        {'step': 'CapturePayment', 'actor': 'worldline', 'optional': True,
         'description': 'If authorization mode was used, merchant captures the payment. This settles the funds - actual money transfer from cardholder to merchant account.',
         'code_ref': 'app.py : capture_payment()', 'api_call': 'capture'},
    ],
    'ServerToServer': [
        {'step': 'Cart & Checkout', 'actor': 'merchant',
         'description': 'Customer selects products. With S2S flow, the merchant collects payment details directly (e.g., via Hosted Tokenization Page or direct card input for PCI-compliant merchants).',
         'code_ref': 'app.js : checkout()', 'api_call': None},
        {'step': 'CreatePayment', 'actor': 'worldline',
         'description': 'Merchant sends CreatePayment with full card details or token, amount, currency, and optional 3DS data. Worldline processes the authorization directly.',
         'code_ref': 'app.py : create_payment_s2s()', 'api_call': 'payments'},
        {'step': '3-D Secure Redirect', 'actor': 'browser',
         'description': 'If 3DS is required, customer is redirected to the issuer bank for authentication. The redirectUrl from the CreatePayment response is used.',
         'code_ref': 'app.js : window.open()', 'api_call': None},
        {'step': 'GetPaymentDetails', 'actor': 'worldline',
         'description': 'After 3DS completion, merchant retrieves payment status using the paymentId. Returns statusCode, payment means, and authorization result.',
         'code_ref': 'app.py : get_payment_status()', 'api_call': 'payments/'},
        {'step': 'CapturePayment', 'actor': 'worldline', 'optional': True,
         'description': 'Capture settles the authorized amount. Same endpoint for both Hosted Checkout and S2S flows.',
         'code_ref': 'app.py : capture_payment()', 'api_call': 'capture'},
    ],
}


def build_journey_steps(txn, logs, flow):
    templates = JOURNEY_TEMPLATES.get(flow, JOURNEY_TEMPLATES['HostedCheckout'])
    steps = []
    for tmpl in templates:
        step = dict(tmpl)
        if tmpl['api_call']:
            match = next((l for l in logs if tmpl['api_call'] in l.get('endpoint', '')), None)
            if match:
                step['log_id'] = match['id']
                step['status_code'] = match.get('status_code')
                step['timestamp'] = match.get('timestamp')
                step['completed'] = True
            else:
                step['completed'] = False
        else:
            step['completed'] = txn.get('status') not in (None, '')
        steps.append(step)
    return steps


# ==================== Pages ====================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/return/success')
def return_success():
    return render_template('return.html', status='success')


@app.route('/return/fail')
def return_fail():
    return render_template('return.html', status='fail')


@app.route('/return/s2s')
def return_s2s():
    return render_template('return.html', status='s2s_return')


# ==================== Config API ====================

@app.route('/api/config', methods=['POST'])
def save_config():
    data = request.json
    required = ['merchant_id', 'api_key', 'api_secret']
    missing = [f for f in required if not data.get(f, '').strip()]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    session['config'] = {
        'merchant_id': data['merchant_id'].strip(),
        'api_key': data['api_key'].strip(),
        'api_secret': data['api_secret'].strip(),
        'base_url': data.get('base_url', 'https://payment.preprod.direct.worldline-solutions.com').strip().rstrip('/'),
        'order_id_prefix': data.get('order_id_prefix', 'WLOP').strip() or 'WLOP',
        'order_id_pattern': data.get('order_id_pattern', 'prefix-uuid').strip(),
        'default_description': data.get('default_description', 'WLOP Explorer Demo Order').strip(),
    }
    return jsonify({'status': 'ok'})


@app.route('/api/config/status')
def config_status():
    config = get_config()
    if config:
        return jsonify({
            'configured': True,
            'merchant_id': config['merchant_id'],
            'base_url': config['base_url'],
            'order_id_prefix': config.get('order_id_prefix', 'WLOP'),
            'order_id_pattern': config.get('order_id_pattern', 'prefix-uuid'),
            'default_description': config.get('default_description', 'WLOP Explorer Demo Order'),
        })
    return jsonify({'configured': False})


# ==================== Payment: Hosted Checkout Flow ====================

@app.route('/api/hosted-checkout/create', methods=['POST'])
def create_hosted_checkout():
    config = get_config()
    if not config:
        return jsonify({'error': 'Not configured. Go to Config tab first.'}), 400

    data = request.json
    store = get_store()
    order_id = generate_order_id(config, 'HC')
    base_url = request.url_root.rstrip('/')
    description = data.get('description') or config.get('default_description', 'WLOP Explorer Demo Order')
    resource = f"/v2/{config['merchant_id']}/hostedcheckouts"

    payload = {
        "order": {
            "amountOfMoney": {
                "amount": data['amount'],
                "currencyCode": data.get('currency', 'EUR')
            },
            "references": {
                "merchantReference": order_id,
                "descriptor": description
            }
        },
        "hostedCheckoutSpecificInput": {
            "returnUrl": f"{base_url}/return/success",
            "locale": "en_GB",
        }
    }

    log_entry = _make_log('CreateHostedCheckout', resource,
        'CreateHostedCheckout creates a payment session on Worldline. The response includes a '
        'hostedCheckoutId (used later to check status) and a redirectUrl (the Worldline-hosted '
        'payment page where the customer enters card details). All payment methods enabled on your '
        'account are offered automatically. Card data never touches the merchant server.',
        order_id)
    log_entry['request'] = payload

    try:
        resp = wlop_request('POST', resource, config, payload)
        log_entry['status_code'] = resp.status_code
        log_entry['response'] = resp.json() if resp.text else {}
        store['logs'].append(log_entry)

        if resp.status_code in (200, 201):
            resp_data = resp.json()
            hc_id = resp_data.get('hostedCheckoutId')
            redirect_url = resp_data.get('redirectUrl') or ''
            # If only partialRedirectUrl, build full URL
            if not redirect_url and resp_data.get('partialRedirectUrl'):
                redirect_url = 'https://' + resp_data['partialRedirectUrl']

            store['transactions'][hc_id] = {
                'hc_id': hc_id, 'order_id': order_id,
                'amount': data['amount'], 'currency': data.get('currency', 'EUR'),
                'items': data.get('items', []),
                'customer_id': data.get('customer_id'),
                'payment_flow': 'HostedCheckout',
                'status': 'CREATED',
                'status_code': 0,
                'created': datetime.utcnow().isoformat() + 'Z',
                'redirect_url': redirect_url,
                'payment_id': None, 'payment_means': None,
                'description': description,
                'returnmac': resp_data.get('RETURNMAC', ''),
            }
            return jsonify({'success': True, 'hc_id': hc_id,
                            'redirect_url': redirect_url,
                            'order_id': order_id, 'log': log_entry})
        else:
            return jsonify({'success': False, 'error': resp.json() if resp.text else {'message': 'Request failed'}, 'log': log_entry}), 400
    except Exception as e:
        log_entry['status_code'] = 0
        log_entry['response'] = {'error': str(e)}
        store['logs'].append(log_entry)
        return jsonify({'success': False, 'error': str(e), 'log': log_entry}), 500


@app.route('/api/hosted-checkout/status', methods=['POST'])
def get_hc_status():
    config = get_config()
    if not config:
        return jsonify({'error': 'Not configured'}), 400
    data = request.json
    hc_id = data.get('hc_id')
    store = get_store()
    order_id = store['transactions'].get(hc_id, {}).get('order_id') if hc_id else None
    resource = f"/v2/{config['merchant_id']}/hostedcheckouts/{hc_id}"

    log_entry = _make_log('GetHostedCheckoutStatus', resource,
        'GetHostedCheckoutStatus retrieves the payment result after the customer returns from the '
        'Worldline payment page. Returns the statusOutput with statusCode, the payment ID, and '
        'payment details including card brand and masked number.',
        order_id)
    log_entry['method'] = 'GET'

    try:
        resp = wlop_request('GET', resource, config)
        log_entry['status_code'] = resp.status_code
        log_entry['response'] = resp.json() if resp.text else {}
        store['logs'].append(log_entry)

        if resp.status_code == 200:
            resp_data = resp.json()
            payment = resp_data.get('createdPaymentOutput', {}).get('payment', {})
            payment_id = payment.get('id')
            status_output = payment.get('statusOutput', {})
            status_code = status_output.get('statusCode', 0)
            payment_output = payment.get('paymentOutput', {})
            card_info = payment_output.get('cardPaymentMethodSpecificOutput', {})

            status_label = WLOP_STATUS_CODES.get(status_code, {}).get('label', f'Code {status_code}')

            if hc_id in store['transactions']:
                store['transactions'][hc_id].update({
                    'status': status_label,
                    'status_code': status_code,
                    'payment_id': payment_id,
                    'payment_means': {
                        'Brand': card_info.get('paymentProductId'),
                        'DisplayText': card_info.get('card', {}).get('cardNumber', ''),
                        'AuthCode': card_info.get('authorisationCode', ''),
                    },
                })
            return jsonify({'success': True, 'data': resp_data,
                            'payment_id': payment_id,
                            'status_code': status_code,
                            'status': status_label,
                            'log': log_entry})
        else:
            if hc_id in store['transactions']:
                store['transactions'][hc_id]['status'] = 'FAILED'
                store['transactions'][hc_id]['status_code'] = 2
            return jsonify({'success': False, 'error': resp.json() if resp.text else {}, 'log': log_entry}), 400
    except Exception as e:
        log_entry['status_code'] = 0
        log_entry['response'] = {'error': str(e)}
        store['logs'].append(log_entry)
        return jsonify({'success': False, 'error': str(e), 'log': log_entry}), 500


# ==================== Payment: Server-to-Server Flow ====================

@app.route('/api/payment/create', methods=['POST'])
def create_payment_s2s():
    config = get_config()
    if not config:
        return jsonify({'error': 'Not configured. Go to Config tab first.'}), 400

    data = request.json
    store = get_store()
    order_id = generate_order_id(config, 'S2S')
    base_url = request.url_root.rstrip('/')
    description = data.get('description') or config.get('default_description', 'WLOP Explorer Demo Order')
    resource = f"/v2/{config['merchant_id']}/payments"

    payload = {
        "cardPaymentMethodSpecificInput": {
            "paymentProductId": data.get('paymentProductId', 1),
            "threeDSecure": {
                "skipAuthentication": False,
                "redirectionData": {
                    "returnUrl": f"{base_url}/return/s2s"
                }
            },
            "authorizationMode": "PRE_AUTHORIZATION"
        },
        "order": {
            "amountOfMoney": {
                "amount": data['amount'],
                "currencyCode": data.get('currency', 'EUR')
            },
            "references": {
                "merchantReference": order_id,
                "descriptor": description
            }
        }
    }

    # If token is provided (from hosted tokenization)
    if data.get('token'):
        payload['cardPaymentMethodSpecificInput']['token'] = data['token']
    # If raw card data is provided (PCI-compliant merchant)
    elif data.get('card'):
        payload['cardPaymentMethodSpecificInput']['card'] = data['card']

    # Add customer info if available
    if data.get('payer'):
        payload['order']['customer'] = {
            'personalInformation': {
                'name': {'firstName': data['payer'].get('FirstName', ''), 'surname': data['payer'].get('LastName', '')}
            },
            'contactDetails': {'emailAddress': data['payer'].get('Email', '')}
        }

    log_entry = _make_log('CreatePayment', resource,
        'CreatePayment (Server-to-Server) sends the payment directly to Worldline. For card payments, '
        'this requires PCI compliance or use of Hosted Tokenization. The response may include a '
        'merchantAction with redirectData if 3-D Secure authentication is required.',
        order_id)
    log_entry['request'] = payload

    try:
        resp = wlop_request('POST', resource, config, payload)
        log_entry['status_code'] = resp.status_code
        log_entry['response'] = resp.json() if resp.text else {}
        store['logs'].append(log_entry)

        if resp.status_code in (200, 201):
            resp_data = resp.json()
            payment = resp_data.get('payment', {})
            payment_id = payment.get('id')
            status_code = payment.get('statusOutput', {}).get('statusCode', 0)
            status_label = WLOP_STATUS_CODES.get(status_code, {}).get('label', f'Code {status_code}')

            # Check for 3DS redirect
            merchant_action = resp_data.get('merchantAction', {})
            redirect_url = ''
            if merchant_action.get('actionType') == 'REDIRECT':
                redirect_url = merchant_action.get('redirectData', {}).get('redirectURL', '')

            store['transactions'][payment_id or order_id] = {
                'hc_id': None, 'order_id': order_id,
                'amount': data['amount'], 'currency': data.get('currency', 'EUR'),
                'items': data.get('items', []),
                'customer_id': data.get('customer_id'),
                'payment_flow': 'ServerToServer',
                'status': status_label,
                'status_code': status_code,
                'created': datetime.utcnow().isoformat() + 'Z',
                'redirect_url': redirect_url,
                'payment_id': payment_id, 'payment_means': None,
                'description': description,
            }
            return jsonify({'success': True, 'payment_id': payment_id,
                            'redirect_url': redirect_url,
                            'status_code': status_code,
                            'order_id': order_id, 'log': log_entry})
        else:
            return jsonify({'success': False, 'error': resp.json() if resp.text else {}, 'log': log_entry}), 400
    except Exception as e:
        log_entry['status_code'] = 0
        log_entry['response'] = {'error': str(e)}
        store['logs'].append(log_entry)
        return jsonify({'success': False, 'error': str(e), 'log': log_entry}), 500


@app.route('/api/payment/status', methods=['POST'])
def get_payment_status():
    config = get_config()
    if not config:
        return jsonify({'error': 'Not configured'}), 400
    data = request.json
    payment_id = data.get('payment_id')
    store = get_store()

    # Find order_id from transaction by payment_id
    order_id = None
    for t in store['transactions'].values():
        if t.get('payment_id') == payment_id:
            order_id = t.get('order_id')
            break

    resource = f"/v2/{config['merchant_id']}/payments/{payment_id}"

    log_entry = _make_log('GetPaymentDetails', resource,
        'GetPaymentDetails retrieves the current status of a payment. Returns the statusCode, '
        'payment output with card details, and the full transaction lifecycle.',
        order_id)
    log_entry['method'] = 'GET'

    try:
        resp = wlop_request('GET', resource, config)
        log_entry['status_code'] = resp.status_code
        log_entry['response'] = resp.json() if resp.text else {}
        store['logs'].append(log_entry)

        if resp.status_code == 200:
            resp_data = resp.json()
            status_code = resp_data.get('statusOutput', {}).get('statusCode', 0)
            status_label = WLOP_STATUS_CODES.get(status_code, {}).get('label', f'Code {status_code}')
            card_info = resp_data.get('paymentOutput', {}).get('cardPaymentMethodSpecificOutput', {})

            # Update the transaction in store
            for key, t in store['transactions'].items():
                if t.get('payment_id') == payment_id:
                    t['status'] = status_label
                    t['status_code'] = status_code
                    t['payment_means'] = {
                        'Brand': card_info.get('paymentProductId'),
                        'DisplayText': card_info.get('card', {}).get('cardNumber', ''),
                        'AuthCode': card_info.get('authorisationCode', ''),
                    }
                    break

            return jsonify({'success': True, 'data': resp_data,
                            'status_code': status_code,
                            'status': status_label,
                            'log': log_entry})
        else:
            return jsonify({'success': False, 'error': resp.json() if resp.text else {}, 'log': log_entry}), 400
    except Exception as e:
        log_entry['status_code'] = 0
        log_entry['response'] = {'error': str(e)}
        store['logs'].append(log_entry)
        return jsonify({'success': False, 'error': str(e), 'log': log_entry}), 500


# ==================== Shared: Capture ====================

@app.route('/api/capture', methods=['POST'])
def capture_payment():
    config = get_config()
    if not config:
        return jsonify({'error': 'Not configured'}), 400
    data = request.json
    payment_id = data.get('payment_id')
    txn_key = data.get('txn_key')
    store = get_store()
    order_id = store['transactions'].get(txn_key, {}).get('order_id') if txn_key else None
    resource = f"/v2/{config['merchant_id']}/payments/{payment_id}/capture"

    payload = {
        "amount": data.get('amount'),
        "isFinal": True
    }

    log_entry = _make_log('CapturePayment', resource,
        'CapturePayment settles the authorized transaction. Authorization only reserved funds; '
        'Capture triggers the actual money transfer. Works for both Hosted Checkout and S2S flows.',
        order_id)
    log_entry['request'] = payload

    try:
        resp = wlop_request('POST', resource, config, payload)
        log_entry['status_code'] = resp.status_code
        log_entry['response'] = resp.json() if resp.text else {}
        store['logs'].append(log_entry)
        if resp.status_code in (200, 201, 204):
            if txn_key and txn_key in store['transactions']:
                store['transactions'][txn_key]['status'] = 'Captured / Paid'
                store['transactions'][txn_key]['status_code'] = 9
            return jsonify({'success': True, 'data': resp.json() if resp.text else {}, 'log': log_entry})
        else:
            return jsonify({'success': False, 'error': resp.json() if resp.text else {}, 'log': log_entry}), 400
    except Exception as e:
        log_entry['status_code'] = 0
        log_entry['response'] = {'error': str(e)}
        store['logs'].append(log_entry)
        return jsonify({'success': False, 'error': str(e), 'log': log_entry}), 500


# ==================== Data API ====================

@app.route('/api/transactions')
def get_transactions():
    store = get_store()
    txns = list(store['transactions'].values())
    for t in txns:
        cid = t.get('customer_id')
        if cid and cid in store['customers']:
            t['customer_name'] = store['customers'][cid]['name']
        else:
            t['customer_name'] = 'Guest'
    txns.sort(key=lambda t: t.get('created', ''), reverse=True)
    return jsonify(txns)


@app.route('/api/logs')
def get_logs():
    return jsonify(get_store()['logs'])


@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    get_store()['logs'] = []
    return jsonify({'status': 'ok'})


@app.route('/api/transactions/clear', methods=['POST'])
def clear_transactions():
    get_store()['transactions'] = {}
    return jsonify({'status': 'ok'})


# ==================== Products API ====================

@app.route('/api/products')
def get_products():
    return jsonify(get_store()['products'])


@app.route('/api/products', methods=['POST'])
def save_product():
    store = get_store()
    data = request.json
    if data.get('id'):
        for p in store['products']:
            if p['id'] == data['id']:
                p.update({k: data[k] for k in ('name', 'description', 'price', 'icon', 'active') if k in data})
                return jsonify(p)
        return jsonify({'error': 'Not found'}), 404
    pid = f"prod_{store['product_seq']:03d}"
    store['product_seq'] += 1
    product = {'id': pid, 'name': data['name'], 'description': data.get('description', ''),
               'price': data['price'], 'currency': data.get('currency', 'EUR'),
               'icon': data.get('icon', '\U0001F4E6'), 'active': True}
    store['products'].append(product)
    return jsonify(product)


@app.route('/api/products/<pid>', methods=['DELETE'])
def delete_product(pid):
    store = get_store()
    store['products'] = [p for p in store['products'] if p['id'] != pid]
    return jsonify({'status': 'ok'})


@app.route('/api/icons')
def get_icons():
    return jsonify(ICONS)


# ==================== Customer CRM API ====================

@app.route('/api/customers')
def get_customers():
    store = get_store()
    customers = list(store['customers'].values())
    for c in customers:
        cid = c['id']
        orders = [t for t in store['transactions'].values() if t.get('customer_id') == cid]
        c['order_count'] = len(orders)
        c['total_spent'] = sum(t.get('amount', 0) for t in orders if t.get('status_code') in (5, 9))
    return jsonify(customers)


@app.route('/api/customers', methods=['POST'])
def save_customer():
    store = get_store()
    data = request.json
    if data.get('id') and data['id'] in store['customers']:
        store['customers'][data['id']].update({k: data[k] for k in ('name', 'email', 'company', 'phone', 'address') if k in data})
        return jsonify(store['customers'][data['id']])
    cid = f"cust_{_uid()}"
    customer = {'id': cid, 'name': data['name'], 'email': data.get('email', ''),
                'company': data.get('company', ''), 'phone': data.get('phone', ''),
                'address': data.get('address', ''), 'created': datetime.utcnow().isoformat() + 'Z', 'notes': []}
    store['customers'][cid] = customer
    return jsonify(customer)


@app.route('/api/customers/<cid>', methods=['DELETE'])
def delete_customer(cid):
    store = get_store()
    store['customers'].pop(cid, None)
    return jsonify({'status': 'ok'})


@app.route('/api/customers/<cid>/notes', methods=['POST'])
def add_note(cid):
    store = get_store()
    if cid not in store['customers']:
        return jsonify({'error': 'Customer not found'}), 404
    note = {'id': _uid(), 'text': request.json['text'], 'timestamp': datetime.utcnow().isoformat() + 'Z'}
    store['customers'][cid]['notes'].insert(0, note)
    return jsonify(note)


@app.route('/api/customers/<cid>/orders')
def customer_orders(cid):
    store = get_store()
    orders = [t for t in store['transactions'].values() if t.get('customer_id') == cid]
    orders.sort(key=lambda o: o.get('created', ''), reverse=True)
    return jsonify(orders)


# ==================== Feature Audit & Journey ====================

@app.route('/api/feature-audit')
def feature_audit():
    total = sum(len(cat['features']) for cat in WLOP_FEATURE_AUDIT)
    implemented = sum(1 for cat in WLOP_FEATURE_AUDIT for f in cat['features'] if f['implemented'])
    return jsonify({
        'categories': WLOP_FEATURE_AUDIT,
        'stats': {
            'total': total,
            'implemented': implemented,
            'coverage_pct': round((implemented / total) * 100) if total > 0 else 0,
        }
    })


@app.route('/api/orders/<order_id>/journey')
def order_journey(order_id):
    store = get_store()
    txn = next((t for t in store['transactions'].values() if t.get('order_id') == order_id), None)
    if not txn:
        return jsonify({'error': 'Order not found'}), 404
    order_logs = sorted(
        [l for l in store['logs'] if l.get('order_id') == order_id],
        key=lambda l: l.get('timestamp', '')
    )
    flow = txn.get('payment_flow', 'HostedCheckout')
    steps = build_journey_steps(txn, order_logs, flow)
    return jsonify({
        'order_id': order_id, 'flow': flow,
        'status': txn.get('status'), 'amount': txn.get('amount'),
        'currency': txn.get('currency'), 'created': txn.get('created'),
        'description': txn.get('description', ''),
        'steps': steps, 'logs': order_logs,
    })


@app.route('/api/status-codes')
def status_codes():
    return jsonify(WLOP_STATUS_CODES)


# ==================== Code Viewer API ====================

SERVICE_PASSWORD = '1235789'

ANNOTATIONS = {
    'app.py': {
        7: 'HMAC-SHA256 is used to sign every API request to Worldline Direct',
        14: 'ProxyFix ensures correct URLs when behind a reverse proxy (Railway, Heroku, etc.)',
        15: 'SECRET_KEY signs session cookies - use a strong random value in production',
        17: 'In-memory store: fast for demo, but lost on restart. Use Redis/DB in production.',
        65: 'wlop_sign: builds the string-to-hash and calculates HMAC-SHA256 with the API Secret',
        67: 'POST requests include Content-Type in the signature, GET requests do not',
        75: 'wlop_request: makes authenticated requests with GCS v1HMAC authorization header',
        81: 'Date header must be in RFC 1123 format for the HMAC signature',
        83: 'Authorization header format: GCS v1HMAC:<API_Key>:<base64_signature>',
        233: 'CreateHostedCheckout: creates a session, returns redirectUrl for the payment page',
        247: 'hostedCheckoutSpecificInput.returnUrl: where customer comes back after payment',
        284: 'GetHostedCheckoutStatus: retrieves payment result using hostedCheckoutId',
        299: 'statusOutput.statusCode: numeric status (5=Authorised, 9=Captured, 2=Declined)',
        339: 'CreatePayment S2S: direct server-to-server payment, needs PCI compliance for card data',
        348: 'threeDSecure.redirectionData: where to send customer for 3DS authentication',
        350: 'authorizationMode PRE_AUTHORIZATION: authorize now, capture later',
        413: 'CapturePayment: same endpoint for both Hosted Checkout and S2S flows',
        416: 'isFinal=true means this is the final capture (no more partial captures)',
    },
    'app.js': {
        1: 'Client-side JavaScript: no frameworks, vanilla JS for full transparency',
        4: 'State object: single source of truth for the entire UI',
        22: 'fmt() converts minor units (cents) to display format: 29900 -> "EUR 299.00"',
        24: 'syntaxHL(): custom JSON syntax highlighter without external libraries',
        43: 'Tab switching: toggles CSS classes, lazy-loads data for each tab',
        50: 'renderShopper(): state machine pattern - shopView controls which screen shows',
        83: 'Products loaded from server API, not hardcoded - merchant can add/remove',
        101: 'Checkout shows customer selector + payment flow choice (HC vs S2S)',
        120: 'checkout(): the main payment flow orchestrator',
        130: 'For S2S flow, token from Hosted Tokenization is needed for PCI compliance',
        140: 'window.open(): payment page opens in popup so split-view stays visible',
        146: 'doStatusCheck(): called after customer returns from Worldline',
        167: 'postMessage listener: popup communicates back to parent window',
        175: 'Fallback: poll for popup close in case postMessage fails',
        188: 'addApiLog(): every API call pushed to dev panel in real-time',
    },
}


@app.route('/api/code/<filename>')
def get_code(filename):
    allowed = {
        'app.py': 'app.py',
        'app.js': os.path.join('static', 'js', 'app.js'),
        'style.css': os.path.join('static', 'css', 'style.css'),
        'index.html': os.path.join('templates', 'index.html'),
    }
    if filename not in allowed:
        return jsonify({'error': 'File not available'}), 404
    filepath = os.path.join(os.path.dirname(__file__), allowed[filename])
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    annotations = ANNOTATIONS.get(filename, {})
    return jsonify({
        'filename': filename, 'content': content,
        'annotations': {str(k): v for k, v in annotations.items()},
        'language': 'python' if filename.endswith('.py') else ('javascript' if filename.endswith('.js') else ('css' if filename.endswith('.css') else 'html'))
    })


@app.route('/api/code/<filename>', methods=['POST'])
def save_code(filename):
    data = request.json
    if data.get('password') != SERVICE_PASSWORD:
        return jsonify({'error': 'Invalid service password'}), 403
    allowed = {
        'app.py': 'app.py',
        'app.js': os.path.join('static', 'js', 'app.js'),
        'style.css': os.path.join('static', 'css', 'style.css'),
        'index.html': os.path.join('templates', 'index.html'),
    }
    if filename not in allowed:
        return jsonify({'error': 'File not available'}), 404
    filepath = os.path.join(os.path.dirname(__file__), allowed[filename])
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data.get('content', ''))
        return jsonify({'status': 'ok', 'message': f'{filename} saved.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/code/unlock', methods=['POST'])
def unlock_code():
    data = request.json
    if data.get('password') == SERVICE_PASSWORD:
        return jsonify({'unlocked': True})
    return jsonify({'unlocked': False, 'error': 'Wrong password'}), 403


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
