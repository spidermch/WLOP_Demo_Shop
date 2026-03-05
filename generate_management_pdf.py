"""Generate Management Overview PDF for WLOP Explorer."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
import os

W, H = A4
PRIMARY = HexColor('#0033A0')
ACCENT = HexColor('#00A0E3')
SUCCESS = HexColor('#10b981')
DARK = HexColor('#1a1d23')
GRAY = HexColor('#5f6672')
LIGHT_BG = HexColor('#f0f2f5')
WHITE = HexColor('#ffffff')

def draw_header(c, y, title, subtitle=None):
    c.setFillColor(PRIMARY)
    c.rect(0, y - 2*mm, W, 18*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(20*mm, y + 5*mm, title)
    if subtitle:
        c.setFont('Helvetica', 9)
        c.drawString(20*mm, y + 0.5*mm, subtitle)
    return y - 8*mm

def draw_section(c, y, title):
    c.setFillColor(PRIMARY)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(20*mm, y, title)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.5)
    c.line(20*mm, y - 3*mm, W - 20*mm, y - 3*mm)
    return y - 10*mm

def draw_bullet(c, y, text, indent=25):
    c.setFillColor(ACCENT)
    c.circle(indent*mm - 3*mm, y + 1.2*mm, 1.5*mm, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.setFont('Helvetica', 9.5)
    words = text.split(' ')
    line = ''
    max_w = W - (indent + 22)*mm
    for word in words:
        test = line + ' ' + word if line else word
        if c.stringWidth(test, 'Helvetica', 9.5) < max_w:
            line = test
        else:
            c.drawString(indent*mm, y, line)
            y -= 4.5*mm
            line = word
    if line:
        c.drawString(indent*mm, y, line)
        y -= 4.5*mm
    return y - 1*mm

def draw_text(c, y, text, font='Helvetica', size=9.5, indent=20, color=DARK):
    c.setFillColor(color)
    c.setFont(font, size)
    words = text.split(' ')
    line = ''
    max_w = W - (indent + 22)*mm
    for word in words:
        test = line + ' ' + word if line else word
        if c.stringWidth(test, font, size) < max_w:
            line = test
        else:
            c.drawString(indent*mm, y, line)
            y -= 4.5*mm
            line = word
    if line:
        c.drawString(indent*mm, y, line)
        y -= 4.5*mm
    return y

def draw_flow_box(c, y, step_num, title, desc):
    box_w = W - 40*mm
    box_h = 18*mm
    x = 20*mm
    c.setFillColor(LIGHT_BG)
    c.roundRect(x, y - box_h, box_w, box_h, 3*mm, fill=1, stroke=0)
    c.setFillColor(PRIMARY)
    c.circle(x + 8*mm, y - box_h/2, 4*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(x + 8*mm, y - box_h/2 - 1.5*mm, str(step_num))
    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(x + 16*mm, y - 5*mm, title)
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 8.5)
    c.drawString(x + 16*mm, y - 11*mm, desc)
    if step_num < 6:
        c.setFillColor(ACCENT)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(W/2, y - box_h - 3*mm, 'v')
    return y - box_h - 7*mm

def generate():
    out = os.path.join(os.path.dirname(__file__), 'WLOP_Explorer_Management_Overview.pdf')
    c = canvas.Canvas(out, pagesize=A4)

    # ===== PAGE 1: Cover =====
    c.setFillColor(PRIMARY)
    c.rect(0, H - 90*mm, W, 90*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 28)
    c.drawString(25*mm, H - 40*mm, 'WLOP Explorer')
    c.setFont('Helvetica', 14)
    c.drawString(25*mm, H - 52*mm, 'Worldline Online Payments Demo Tool')
    c.setFont('Helvetica', 10)
    c.drawString(25*mm, H - 65*mm, 'Management Overview | Sales Enablement | Product Brief')
    c.setFillColor(ACCENT)
    c.rect(25*mm, H - 72*mm, 40*mm, 1*mm, fill=1, stroke=0)

    y = H - 110*mm
    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(25*mm, y, 'What is WLOP Explorer?')
    y -= 8*mm
    y = draw_text(c, y, 'WLOP Explorer is an interactive demo application for Worldline Online Payments (Direct API). It provides a complete e-commerce experience with live API debugging, allowing sales teams and technical evaluators to see exactly how the Worldline Direct payment integration works - from cart to capture.', indent=25, color=GRAY)

    y -= 8*mm
    c.setFillColor(DARK)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(25*mm, y, 'Target Audience')
    y -= 8*mm
    for item in ['Sales teams demoing Worldline Direct to enterprise merchants',
                 'Pre-sales engineers conducting technical evaluations',
                 'Partner integrators learning the HMAC-authenticated API',
                 'Training sessions for payment operations teams',
                 'Merchant CTOs evaluating Worldline Direct vs. competitors']:
        y = draw_bullet(c, y, item)

    c.setFillColor(GRAY)
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, 12*mm, 'Confidential - Worldline / WLOP Explorer Management Overview')
    c.drawRightString(W - 20*mm, 12*mm, 'Page 1 of 3')
    c.showPage()

    # ===== PAGE 2: SMART Goals & USPs =====
    y = H - 15*mm
    y = draw_header(c, y, 'SMART Goals & Unique Selling Points')

    y -= 10*mm
    y = draw_section(c, y, 'SMART Goals')

    goals = [
        ('Specific', 'Enable sales engineers to demonstrate the complete Worldline Direct payment flow (Hosted Checkout + Server-to-Server) in under 20 minutes, replacing static slide decks with live, interactive demos.'),
        ('Measurable', 'Increase demo-to-proposal conversion rate by 35% within 6 months of deployment. Track number of demos, time-to-close, and merchant satisfaction scores.'),
        ('Achievable', 'Single .exe deployment requires only PSPID, API Key, and API Secret. No server infrastructure, Docker, or cloud setup. Works on any Windows laptop.'),
        ('Relevant', 'Supports Worldline\'s enterprise merchant acquisition by making the Direct API\'s HMAC authentication, Hosted Checkout, and S2S flows tangible during evaluation.'),
        ('Time-bound', 'Roll out to all WLOP sales teams by end of Q2 2026. Collect feedback and iterate by Q3 2026.'),
    ]
    for label, desc in goals:
        c.setFillColor(PRIMARY)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(20*mm, y, label)
        y -= 5*mm
        y = draw_text(c, y, desc, indent=20, color=GRAY, size=8.5)
        y -= 3*mm

    y -= 5*mm
    y = draw_section(c, y, 'Unique Selling Points (USPs)')

    usps = [
        'Dual Payment Flows: Hosted Checkout (PCI-light) and Server-to-Server (full control) in one demo, showing the right solution for every merchant profile.',
        'HMAC-SHA256 Authentication: Live demonstration of the GCS v1HMAC signature scheme - the actual production authentication method.',
        'Split-Screen Experience: Customer shopping journey + real-time API debugger side-by-side for dual-audience presentations.',
        'Full E-Commerce Lifecycle: Products, cart, customer details form, payment, authorization, capture - the complete flow.',
        'Zero-Infrastructure: Ships as a standalone executable. No servers, databases, or DevOps required.',
        'Feature Audit Dashboard: Visual coverage of Worldline Direct API capabilities with implementation status.',
        'Order Journey Timeline: Step-by-step trace through each payment with request/response at every stage.',
        'Source Code Viewer: Annotated source code showing exactly how each API integration works.',
        'Remote Error Diagnostics: Automatic error logging to debug.log for support team troubleshooting.',
    ]
    for usp in usps:
        y = draw_bullet(c, y, usp)
        if y < 25*mm:
            c.setFillColor(GRAY)
            c.setFont('Helvetica', 7)
            c.drawString(20*mm, 12*mm, 'Confidential - Worldline / WLOP Explorer Management Overview')
            c.drawRightString(W - 20*mm, 12*mm, 'Page 2 of 3')
            c.showPage()
            y = H - 20*mm

    c.setFillColor(GRAY)
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, 12*mm, 'Confidential - Worldline / WLOP Explorer Management Overview')
    c.drawRightString(W - 20*mm, 12*mm, 'Page 2 of 3')
    c.showPage()

    # ===== PAGE 3: High-Level Flow =====
    y = H - 15*mm
    y = draw_header(c, y, 'High-Level End-User Flow')

    y -= 12*mm
    steps = [
        ('Browse & Shop', 'End user browses product catalog, selects items, adds to cart'),
        ('Customer Details', 'User enters name, email, address - mandatory checkout step'),
        ('Select Payment Flow', 'Choose Hosted Checkout (redirect) or Server-to-Server (direct API)'),
        ('Secure Payment', 'User pays on Worldline-hosted page or via tokenized S2S flow'),
        ('Status Verification', 'System checks payment status via GetHostedCheckoutStatus or GetPaymentDetails'),
        ('Capture & Settlement', 'Merchant captures the authorized amount - funds transfer initiated'),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        y = draw_flow_box(c, y, i, title, desc)

    y -= 5*mm
    y = draw_section(c, y, 'Technical Architecture')
    y -= 2*mm

    arch_items = [
        'Backend: Python/Flask with HMAC-SHA256 request signing (GCS v1HMAC)',
        'Frontend: Vanilla JavaScript SPA - no frameworks, full transparency',
        'API Auth: HMAC signature with API Key + Secret (Worldline Direct)',
        'Security: Service password for code editing, session config, debug logging',
        'Deployment: PyInstaller .exe / Heroku / Railway / any Python host',
        'Debug: Automatic error logging to debug.log with full context and tracebacks',
    ]
    for item in arch_items:
        y = draw_bullet(c, y, item)

    y -= 8*mm
    c.setFillColor(PRIMARY)
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(W/2, y, 'Ready to accelerate your payment demos?')
    y -= 6*mm
    c.setFillColor(GRAY)
    c.setFont('Helvetica', 9)
    c.drawCentredString(W/2, y, 'Contact your Worldline sales representative for deployment and credentials.')

    c.setFillColor(GRAY)
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, 12*mm, 'Confidential - Worldline / WLOP Explorer Management Overview')
    c.drawRightString(W - 20*mm, 12*mm, 'Page 3 of 3')

    c.save()
    print(f'Generated: {out}')

if __name__ == '__main__':
    generate()
