"""Generate Worldline WLOP Explorer PDF Guides:
   1. Deployment Guide
   2. User Guide
Both with Worldline branding and version history.
"""

from fpdf import FPDF
import os

# ---- Brand Constants ----
WL_RED = (228, 0, 43)
WL_NAVY = (26, 31, 54)
WL_DARK = (30, 32, 40)
WL_GREY = (90, 95, 105)
WL_LIGHT = (245, 247, 250)
WL_WHITE = (255, 255, 255)
WL_GREEN = (16, 185, 129)
WL_AMBER = (180, 83, 9)

VERSION = "1.0.0"
DATE = "March 2026"


class WLGuide(FPDF):
    """Base PDF class with Worldline branding."""

    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 15, 20)

    def header(self):
        if self.page_no() == 1:
            return
        self._draw_logo_small(self.l_margin, 8)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*WL_GREY)
        self.set_xy(self.l_margin + 50, 8)
        self.cell(0, 6, self.doc_title, align="L")
        self.cell(0, 6, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*WL_RED)
        self.line(self.l_margin, 16, self.w - self.r_margin, 16)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 6.5)
        self.set_text_color(*WL_GREY)
        self.cell(0, 8, f"Worldline  |  WLOP Explorer v{VERSION}  |  Confidential", align="C")

    # ---- Logo Drawing ----
    def _draw_logo(self, x, y, scale=1.0):
        """Draw Worldline logo: red bar + WORLDLINE text."""
        bw = 5 * scale
        bh = 32 * scale
        self.set_fill_color(*WL_RED)
        self.rect(x, y, bw, bh, "F")
        self.set_font("Helvetica", "B", int(22 * scale))
        self.set_text_color(*WL_NAVY)
        self.set_xy(x + bw + 5 * scale, y + 8 * scale)
        self.cell(0, bh * 0.6, "WORLDLINE", new_x="LMARGIN", new_y="NEXT")

    def _draw_logo_small(self, x, y):
        self.set_fill_color(*WL_RED)
        self.rect(x, y, 2.5, 8, "F")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*WL_NAVY)
        self.set_xy(x + 4, y + 1)
        self.cell(40, 6, "WORLDLINE")

    # ---- Cover Page ----
    def cover_page(self, subtitle, audience):
        self.add_page()
        # Red top bar
        self.set_fill_color(*WL_RED)
        self.rect(0, 0, self.w, 4, "F")
        # Logo
        self.ln(35)
        self._draw_logo(self.l_margin, self.get_y(), 1.3)
        self.ln(55)
        # Title
        self.set_font("Helvetica", "B", 30)
        self.set_text_color(*WL_NAVY)
        self.cell(0, 13, "WLOP Explorer", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*WL_GREY)
        self.cell(0, 10, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
        # Red line
        self.ln(4)
        self.set_draw_color(*WL_RED)
        self.set_line_width(0.8)
        self.line(65, self.get_y(), 145, self.get_y())
        self.set_line_width(0.2)
        self.ln(8)
        # Version
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*WL_DARK)
        self.cell(0, 7, f"Version {VERSION}  |  {DATE}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(25)
        # Audience
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*WL_GREY)
        self.cell(0, 6, audience, align="C", new_x="LMARGIN", new_y="NEXT")
        # Bottom bar
        self.set_fill_color(*WL_RED)
        self.rect(0, self.h - 4, self.w, 4, "F")

    # ---- Reusable Elements ----
    def section(self, num, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*WL_NAVY)
        self.cell(0, 9, f"{num}.  {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*WL_RED)
        self.line(self.l_margin, self.get_y(), self.l_margin + 50, self.get_y())
        self.ln(5)

    def sub(self, title):
        self.ln(1.5)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*WL_DARK)
        self.cell(0, 6.5, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def txt(self, t):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*WL_DARK)
        self.multi_cell(0, 5.2, t)
        self.ln(0.8)

    def code(self, lines):
        self.set_fill_color(*WL_LIGHT)
        self.set_font("Courier", "", 8.5)
        self.set_text_color(*WL_DARK)
        w = self.w - self.l_margin - self.r_margin
        for ln in lines:
            self.set_x(self.l_margin)
            self.cell(w, 5.5, f"  {ln}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2.5)

    def bullet(self, text, bold=""):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*WL_DARK)
        self.set_x(self.get_x() + 3)
        self.cell(4, 5.2, "-")
        if bold:
            self.set_font("Helvetica", "B", 9.5)
            self.cell(self.get_string_width(bold) + 1, 5.2, bold)
            self.set_font("Helvetica", "", 9.5)
        self.multi_cell(0, 5.2, text)
        self.ln(0.4)

    def num(self, n, text):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(*WL_RED)
        self.set_x(self.get_x() + 2)
        self.cell(7, 5.5, f"{n}.")
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*WL_DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(0.8)

    def tip(self, title, text):
        self.ln(1.5)
        self.set_fill_color(236, 253, 245)
        x0, w = self.l_margin, self.w - self.l_margin - self.r_margin
        y0 = self.get_y()
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*WL_GREEN)
        self.set_x(x0)
        self.cell(w, 5.5, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(5, 80, 60)
        self.set_x(x0)
        self.multi_cell(w, 4.8, f"  {text}", fill=True)
        y1 = self.get_y()
        self.set_draw_color(*WL_GREEN)
        self.rect(x0, y0, w, y1 - y0)
        self.ln(3)

    def warn(self, title, text):
        self.ln(1.5)
        self.set_fill_color(255, 251, 235)
        x0, w = self.l_margin, self.w - self.l_margin - self.r_margin
        y0 = self.get_y()
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*WL_AMBER)
        self.set_x(x0)
        self.cell(w, 5.5, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(120, 60, 0)
        self.set_x(x0)
        self.multi_cell(w, 4.8, f"  {text}", fill=True)
        y1 = self.get_y()
        self.set_draw_color(*WL_AMBER)
        self.rect(x0, y0, w, y1 - y0)
        self.ln(3)

    def page_check(self):
        if self.get_y() > 248:
            self.add_page()

    def toc_entry(self, num, title):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*WL_DARK)
        self.cell(8, 7, f"{num}.")
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    def version_entry(self, ver, date, items):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WL_NAVY)
        self.cell(0, 7, f"v{ver}  -  {date}", new_x="LMARGIN", new_y="NEXT")
        for it in items:
            self.bullet(it)
        self.ln(2)


# ============================================================
#  DEPLOYMENT GUIDE
# ============================================================
def build_deployment_guide():
    pdf = WLGuide("WLOP Explorer - Deployment Guide", "P", "mm", "A4")
    pdf.cover_page("Deployment Guide", "For: Worldline colleagues - Sales, Operations, Developers, Merchants")

    # TOC
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*WL_NAVY)
    pdf.cell(0, 11, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    for n, t in [("1", "One-Click Start (Recommended)"), ("2", "Prerequisites (Developer Setup)"), ("3", "Check Your System"),
                  ("4", "Get the Project Files"), ("5", "Run from Source"), ("6", "Deploy to Railway"),
                  ("7", "Configure WLOP Credentials"), ("8", "Authentication (HMAC-SHA256)"),
                  ("9", "Test Card Numbers"), ("10", "Troubleshooting"), ("11", "Project File Overview"),
                  ("12", "Version History")]:
        pdf.toc_entry(n, t)

    # 1 - One-Click Start
    pdf.add_page()
    pdf.section("1", "One-Click Start (Recommended)")
    pdf.txt("The fastest way to run WLOP Explorer. No Python installation needed, no command line, no setup - just one double-click.")
    pdf.ln(2)
    pdf.sub("How to Start")
    pdf.num(1, "Locate the file WLOP_Explorer.exe in the project folder")
    pdf.num(2, "Double-click it")
    pdf.num(3, "A console window opens showing 'WLOP Explorer starting...'")
    pdf.num(4, "Your browser opens automatically at http://localhost:5001")
    pdf.num(5, "Done! Go to the Config tab and enter your Worldline credentials.")
    pdf.ln(2)
    pdf.tip("ONE CLICK - THAT'S IT", "The .exe bundles Python, Flask, and all dependencies. Nothing else to install. Just double-click and go.")
    pdf.ln(2)
    pdf.sub("How to Stop")
    pdf.txt("Close the console window (the black terminal), or press CTRL+C in it.")
    pdf.sub("Windows SmartScreen Warning")
    pdf.txt("On first launch, Windows may show 'Windows protected your PC'. This is normal for unsigned executables. Click 'More info' and then 'Run anyway'.")
    pdf.sub("When to Use the .exe vs Python")
    pdf.bullet("Use the .exe for demos, presentations, quick access - no setup required", "Use .exe: ")
    pdf.bullet("Use Python if you want to modify the source code or deploy to a server", "Use Python: ")
    pdf.sub("Running Both Apps Side by Side")
    pdf.txt("Saferpay Explorer runs on port 5000, WLOP Explorer on port 5001. You can run both .exe files at the same time!")
    pdf.warn("NOTE", "The .exe runs on the machine where you double-click it. For cloud deployment (Railway), use the Python source method (Section 5-6).")

    # 2 - Prerequisites (Developer Setup)
    pdf.add_page()
    pdf.section("2", "Prerequisites (Developer Setup)")
    pdf.txt("Only needed if you want to run from source code or deploy to a server. Skip this if you use the .exe.")
    pdf.sub("Required Software")
    pdf.bullet("Python 3.9 or higher - https://www.python.org/downloads/", "Python 3.9+: ")
    pdf.txt('    IMPORTANT: Check "Add Python to PATH" during installation!')
    pdf.bullet("pip (comes with Python)", "pip: ")
    pdf.bullet("Git - https://git-scm.com/downloads", "Git: ")
    pdf.bullet("A web browser (Chrome, Edge, Firefox)", "Browser: ")
    pdf.sub("For Railway Deployment (Optional)")
    pdf.bullet("Railway account - https://railway.app", "Account: ")
    pdf.bullet("Railway CLI - details in Section 6", "CLI: ")
    pdf.sub("For Worldline Direct API Access")
    pdf.bullet("Merchant ID (PSPID) - from the Merchant Portal", "PSPID: ")
    pdf.bullet("API Key ID - from Merchant Portal > Developer > Payment API", "API Key: ")
    pdf.bullet("API Secret - shown once on creation (save immediately!)", "API Secret: ")
    pdf.bullet("Merchant Portal: https://preprod.account.worldline-solutions.com", "Portal: ")
    pdf.tip("TIP", "You can explore the UI without credentials. The Config tab will prompt when needed.")

    # 3 - Check Your System
    pdf.add_page()
    pdf.section("3", "Check Your System")
    pdf.txt("Open CMD or PowerShell and verify:")
    pdf.sub("Python")
    pdf.code(["python --version", "# Expected: Python 3.9+ (e.g. Python 3.12.8)"])
    pdf.sub("pip")
    pdf.code(["pip --version", "# If not found: python -m pip --version"])
    pdf.sub("Git")
    pdf.code(["git --version"])
    pdf.sub("Network")
    pdf.code(["curl https://payment.preprod.direct.worldline-solutions.com --head"])
    pdf.warn("CORPORATE PROXY", "Set HTTPS_PROXY and HTTP_PROXY env vars if behind a proxy.")

    # 4 - Get the Project Files
    pdf.section("4", "Get the Project Files")
    pdf.txt("Only needed if running from source. If using the .exe, skip to Section 7.")
    pdf.sub("Option A: Git Clone")
    pdf.code(["git clone <REPOSITORY_URL>", "cd WLOP_Demo_Shop"])
    pdf.sub("Option B: Copy Folder")
    pdf.num(1, "Extract ZIP to e.g. C:\\Projects\\WLOP_Demo_Shop")
    pdf.num(2, "cd C:\\Projects\\WLOP_Demo_Shop")
    pdf.sub("Verify Structure")
    pdf.code(["WLOP_Explorer.exe   <-- One-click start!", "app.py  requirements.txt  Procfile  runtime.txt", "templates/  static/  generate_guides.py"])

    # 5 - Run from Source
    pdf.add_page()
    pdf.section("5", "Run from Source (Developer Method)")
    pdf.txt("Alternative to the .exe. Use this if you want to modify the code or need a custom setup.")
    pdf.sub("Step 1: Virtual Environment")
    pdf.code(["python -m venv venv", "venv\\Scripts\\activate        # Windows CMD", "source venv/bin/activate     # macOS/Linux"])
    pdf.sub("Step 2: Install Dependencies")
    pdf.code(["pip install -r requirements.txt"])
    pdf.sub("Step 3: Start the App")
    pdf.code(["python app.py", "# Running on http://127.0.0.1:5001"])
    pdf.sub("Step 4: Open Browser")
    pdf.code(["http://localhost:5001"])
    pdf.tip("TIP", "The WLOP Explorer runs on port 5001 by default (port 5000 is used by the Saferpay Explorer). Press CTRL+C to stop.")

    # 6 - Deploy to Railway
    pdf.add_page()
    pdf.section("6", "Deploy to Railway")
    pdf.txt("Railway is a cloud platform. The app includes Procfile + runtime.txt for auto-detection.")
    pdf.sub("CLI Method")
    pdf.num(1, "Sign up at https://railway.app")
    pdf.num(2, "Install CLI: npm install -g @railway/cli")
    pdf.num(3, "railway login")
    pdf.num(4, "cd WLOP_Demo_Shop && railway init")
    pdf.num(5, "railway variables set SECRET_KEY=your-random-key")
    pdf.num(6, "railway up")
    pdf.num(7, "railway open")
    pdf.sub("Dashboard Method (No CLI)")
    pdf.num(1, "Push to GitHub")
    pdf.num(2, "railway.app > New Project > Deploy from GitHub")
    pdf.num(3, "Add SECRET_KEY in Variables tab")
    pdf.num(4, "Settings > Networking > Generate Domain")
    pdf.tip("TIP", "GitHub pushes trigger automatic redeployment.")

    # 7 - Configure WLOP Credentials
    pdf.page_check()
    pdf.section("7", "Configure WLOP Credentials")
    pdf.txt("Open the app > Config tab. Enter:")
    pdf.bullet("Your PSPID from the Merchant Portal", "Merchant ID (PSPID): ")
    pdf.bullet("API Key ID from Developer > Payment API section", "API Key: ")
    pdf.bullet("Secret API Key - shown ONCE on creation (save immediately!)", "API Secret: ")
    pdf.bullet("Test: payment.preprod.direct.worldline-solutions.com (default)", "Base URL: ")
    pdf.warn("API SECRET", "The API Secret disappears after 60 seconds in the portal. Copy it immediately when created!")
    pdf.warn("SESSION STORAGE", "Credentials stored in browser session only. Re-enter after restart.")

    # 8 - Authentication (HMAC-SHA256)
    pdf.add_page()
    pdf.section("8", "Authentication (HMAC-SHA256)")
    pdf.txt("The Worldline Direct API uses HMAC-SHA256 for authentication. Every request is signed with your API Secret.")
    pdf.sub("How It Works")
    pdf.num(1, "A 'string-to-hash' is built from: HTTP method, Content-Type (POST only), Date, and resource path.")
    pdf.num(2, "This string is signed using HMAC-SHA256 with your API Secret as the key.")
    pdf.num(3, "The signature is Base64-encoded and sent in the Authorization header.")
    pdf.sub("Authorization Header Format")
    pdf.code(["Authorization: GCS v1HMAC:<API_Key>:<base64_signature>"])
    pdf.sub("String-to-Hash (POST)")
    pdf.code(["POST", "application/json; charset=utf-8", "Mon, 01 Mar 2026 12:00:00 GMT", "/v2/YourPSPID/hostedcheckouts", ""])
    pdf.sub("String-to-Hash (GET)")
    pdf.code(["GET", "Mon, 01 Mar 2026 12:00:00 GMT", "/v2/YourPSPID/hostedcheckouts/hcId", ""])
    pdf.tip("HANDLED AUTOMATICALLY", "The WLOP Explorer handles all signing automatically. You just need to provide the API Key and Secret in the Config tab.")

    # 9 - Test Card Numbers
    pdf.add_page()
    pdf.section("9", "Test Card Numbers")
    for brand, num in [("Visa", "4012 0000 3333 0026"), ("Mastercard", "5399 9999 9999 9999"),
                        ("American Express", "3714 496353 98431")]:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*WL_DARK)
        pdf.cell(38, 5.5, f"  {brand}")
        pdf.set_font("Courier", "", 9.5)
        pdf.cell(0, 5.5, num, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.txt("Expiry: any future date (e.g. 12/2030)  |  CVC: any 3 digits")
    pdf.tip("TIP", "These are Worldline preprod test cards. Use them only on the preprod (test) environment.")

    # 10 - Troubleshooting
    pdf.section("10", "Troubleshooting")
    pdf.sub("'python' not recognized")
    pdf.txt("Reinstall Python with 'Add to PATH' checked.")
    pdf.sub("pip SSL/proxy errors")
    pdf.code(["pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org"])
    pdf.sub("Port 5001 in use")
    pdf.code(["set PORT=8081 && python app.py"])
    pdf.sub("Popup blocked")
    pdf.txt("Allow popups for localhost. Fallback link is shown in the UI.")
    pdf.sub("401 / HMAC Signature Error")
    pdf.txt("Check API Key and API Secret in Config tab. Ensure they match your PSPID. Verify your system clock is accurate (HMAC uses Date header).")
    pdf.sub("403 Forbidden / Invalid PSPID")
    pdf.txt("Ensure the Merchant ID (PSPID) matches your account. Check that API credentials belong to the correct environment (test vs production).")

    # 11 - Project File Overview
    pdf.add_page()
    pdf.section("11", "Project File Overview")
    for f, d in [("WLOP_Explorer.exe", "One-click launcher - double-click to start!"),
                  ("app.py", "Flask backend: HMAC auth, payment logic, CRM, products, code viewer"),
                  ("run.py", "Launcher script used by the .exe (auto-opens browser)"),
                  ("requirements.txt", "Dependencies: Flask, requests, gunicorn"),
                  ("Procfile", "Railway start command (gunicorn)"),
                  ("templates/index.html", "SPA with 6 tabs: Explorer, Products, Orders, Customers, Code, Config"),
                  ("templates/return.html", "Popup return page after payment"),
                  ("static/js/app.js", "Client logic: cart, payments, CRM, code viewer"),
                  ("static/css/style.css", "Styling: responsive layout, dark dev console"),
                  ("static/img/", "Worldline logo assets"),
                  ("generate_guides.py", "PDF guide generator script")]:
        pdf.set_font("Courier", "B", 8.5)
        pdf.set_text_color(*WL_RED)
        pdf.cell(42, 5.5, f)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*WL_DARK)
        pdf.multi_cell(0, 5.5, d)
        pdf.ln(0.5)

    # 12 - Version History
    pdf.add_page()
    pdf.section("12", "Version History")
    pdf.version_entry("1.0.0", "March 2026", [
        "Initial release: Explorer split-view (Shopper + Developer)",
        "Hosted Checkout flow: CreateHostedCheckout, GetStatus, Capture",
        "Server-to-Server flow: CreatePayment, GetPaymentDetails, Capture",
        "HMAC-SHA256 authentication for all API requests",
        "Product catalog management (add, edit, delete, icon picker)",
        "Customer CRM (contacts, notes, search, lifetime value)",
        "Order Journey Viewer with timeline visualization",
        "Feature Audit with coverage donut chart",
        "Code Viewer with 20+ educational annotations",
        "Configurable Order ID patterns (prefix, UUID, timestamp, flow-tagged)",
        "Configuration tab with PSPID, API Key, API Secret, Base URL",
        "Railway deployment support (Procfile, runtime.txt)",
    ])
    pdf.sub("Planned")
    pdf.bullet("Cancel payment (POST /v2/{mid}/payments/{id}/cancel)")
    pdf.bullet("Refund payment (POST /v2/{mid}/payments/{id}/refund)")
    pdf.bullet("Hosted Tokenization Page integration")
    pdf.bullet("Recurring/subscription payment demo")
    pdf.bullet("Pay-by-Link generation")
    pdf.bullet("Dynamic Currency Conversion (DCC)")
    pdf.bullet("Webhook/notification handling demo")
    pdf.bullet("Multi-currency support and display")

    pdf.output("WLOP_Explorer_Deployment_Guide.pdf")
    print("  -> WLOP_Explorer_Deployment_Guide.pdf")


# ============================================================
#  USER GUIDE
# ============================================================
def build_user_guide():
    pdf = WLGuide("WLOP Explorer - User Guide", "P", "mm", "A4")
    pdf.cover_page("User Guide", "For: Worldline Sales, Operations, Developers, Technical Merchants")

    # TOC
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*WL_NAVY)
    pdf.cell(0, 11, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    for n, t in [("1", "Introduction"), ("2", "Quick Start"), ("3", "Explorer Tab"),
                  ("4", "Products Tab"), ("5", "Orders Tab"), ("6", "Customers (CRM) Tab"),
                  ("7", "Code Tab"), ("8", "Configuration Tab"),
                  ("9", "Payment Flows Explained"), ("10", "HMAC Authentication"),
                  ("11", "API Reference"), ("12", "Status Codes"),
                  ("13", "Test Cards"), ("14", "Version History")]:
        pdf.toc_entry(n, t)

    # 1 - Introduction
    pdf.add_page()
    pdf.section("1", "Introduction")
    pdf.sub("What is WLOP Explorer?")
    pdf.txt("WLOP Explorer is an educational demo web application that visualizes the Worldline Online Payments (Direct API) payment flow from multiple perspectives simultaneously. It combines a demo webshop, live API debugger, merchant dashboard, customer CRM, and annotated source code viewer in one interactive tool.")
    pdf.sub("Who is it for?")
    pdf.bullet("Sales teams - demonstrate Worldline Online Payments to prospects in live meetings")
    pdf.bullet("Operations teams - understand the payment flow end-to-end")
    pdf.bullet("Developers - learn the Direct API with real requests/responses and annotated code")
    pdf.bullet("Merchants - see what happens behind the scenes when a customer pays")
    pdf.sub("Key Features")
    pdf.bullet("Split-screen: Shopper view + Developer API console side by side")
    pdf.bullet("Two payment flows: Hosted Checkout (simple) and Server-to-Server (advanced)")
    pdf.bullet("Product catalog management with add/edit/delete")
    pdf.bullet("Customer CRM with notes, search, and order history")
    pdf.bullet("Order Journey Viewer with timeline showing merchant code vs API calls")
    pdf.bullet("Feature Audit showing implemented vs available API features")
    pdf.bullet("Annotated source code viewer for learning")
    pdf.bullet("Real Worldline preprod environment integration")
    pdf.bullet("HMAC-SHA256 authentication - the real production auth method")
    pdf.sub("Architecture")
    pdf.txt("Backend: Python Flask | Frontend: Vanilla JavaScript (no frameworks) | Auth: HMAC-SHA256 | Deployment: Railway-ready | API: Worldline Direct API v2")

    # 2 - Quick Start
    pdf.add_page()
    pdf.section("2", "Quick Start")
    pdf.txt("Get up and running in 5 steps:")
    pdf.ln(2)
    pdf.num(1, "Open the app in your browser (http://localhost:5001 or your Railway URL)")
    pdf.num(2, "Go to the Config tab and enter your Worldline Direct API credentials (PSPID, API Key, API Secret)")
    pdf.num(3, "Switch to the Explorer tab - you'll see the shop on the left, API console on the right")
    pdf.num(4, "Add products to the cart and click 'Pay Now'")
    pdf.num(5, "Complete payment with a test card and watch the API flow in real-time!")
    pdf.ln(4)
    pdf.tip("FIRST TIME?", "If you don't have credentials yet, you can still browse the UI. The app will prompt you to configure credentials when you try to make a payment.")
    pdf.ln(2)
    pdf.sub("Navigation")
    pdf.txt("The app has 6 main tabs in the top navigation bar:")
    pdf.ln(1)
    pdf.bullet("The payment flow visualizer with split-screen", "Explorer: ")
    pdf.bullet("Manage your product catalog", "Products: ")
    pdf.bullet("View transactions, stats, journey viewer, and feature audit", "Orders: ")
    pdf.bullet("Customer relationship management", "Customers: ")
    pdf.bullet("View annotated source code", "Code: ")
    pdf.bullet("API credentials and environment settings", "Config: ")

    # 3 - Explorer
    pdf.add_page()
    pdf.section("3", "Explorer Tab")
    pdf.txt("The Explorer is the heart of WLOP Explorer. It shows the customer journey (left) and the technical API flow (right) simultaneously.")
    pdf.sub("Shopper View (Left Panel)")
    pdf.txt("This simulates what a customer sees on a merchant's webshop:")
    pdf.num(1, "BROWSE: View the product catalog with prices in EUR. Click 'Add to Cart' to build your order.")
    pdf.num(2, "CART: Review items, remove unwanted ones. Select a customer from CRM (optional) and choose a payment integration method.")
    pdf.num(3, "PAYMENT: Click 'Pay Now'. A popup opens with the Worldline payment page. Enter a test card number.")
    pdf.num(4, "RESULT: See whether the payment was authorized. Optionally capture it.")
    pdf.sub("Developer View (Right Panel)")
    pdf.txt("Shows every API call in real-time as it happens:")
    pdf.bullet("Each call shows: HTTP method, endpoint URL, status code, timestamp")
    pdf.bullet("Click any entry to expand and see the full JSON request and response")
    pdf.bullet("Educational annotations explain what each API call does and why")
    pdf.bullet("Color-coded: blue = Hosted Checkout, pink = Server-to-Server, green = Capture")
    pdf.sub("Flow Indicator")
    pdf.txt("The progress bar at the top of the shopper view shows where you are in the flow: Browse > Cart > Initialize > Payment Page > Status Check > Capture")
    pdf.sub("Split Handle")
    pdf.txt("Drag the divider between panels to resize them. Useful when presenting or when you want more space for the JSON output.")
    pdf.sub("Payment Integration Choice")
    pdf.txt("At checkout, you choose between two Worldline integration methods:")
    pdf.bullet("All-in-one redirect. Worldline shows all enabled payment methods on a hosted page. Simplest integration. Uses CreateHostedCheckout + GetHostedCheckoutStatus.", "Hosted Checkout: ")
    pdf.bullet("Direct server-to-server payment. Requires PCI compliance or Hosted Tokenization for card data. Uses CreatePayment + GetPaymentDetails.", "Server-to-Server: ")

    # 4 - Products
    pdf.add_page()
    pdf.section("4", "Products Tab")
    pdf.txt("Manage the product catalog that appears in the shop. The app starts with 4 demo products (Swiss-themed) but you can customize freely.")
    pdf.sub("Adding a Product")
    pdf.num(1, "Click '+ Add Product' button")
    pdf.num(2, "Enter the product name (required) and price in EUR")
    pdf.num(3, "Add an optional description")
    pdf.num(4, "Pick an icon from the icon grid (20 options)")
    pdf.num(5, "Click 'Add Product'")
    pdf.sub("Editing a Product")
    pdf.txt("Click the pencil icon on any product card. The form pre-fills with the current values. Make changes and click 'Save Changes'.")
    pdf.sub("Deactivating / Deleting")
    pdf.bullet("X icon: Deactivates the product (hidden from shop, can reactivate later)")
    pdf.bullet("Trash icon: Permanently deletes the product")
    pdf.tip("TIP", "Deactivate seasonal products instead of deleting them - you can reactivate them later without re-entering all the details.")

    # 5 - Orders
    pdf.add_page()
    pdf.section("5", "Orders Tab")
    pdf.txt("The merchant's view of all transactions processed through the shop.")
    pdf.sub("Dashboard Stats")
    pdf.txt("Four metric cards at the top show:")
    pdf.bullet("Total number of payment attempts", "Total Orders: ")
    pdf.bullet("Sum of all transaction amounts", "Total Volume: ")
    pdf.bullet("Payments approved but not yet settled (statusCode 5)", "Authorised: ")
    pdf.bullet("Payments settled (statusCode 9)", "Captured: ")
    pdf.sub("Transaction Table")
    pdf.txt("Shows all transactions with: Order ID, customer name, amount, status badge, integration flow (HC or S2S), payment method, time, and action buttons.")
    pdf.sub("Capturing Payments")
    pdf.txt("Authorized transactions show a green 'Capture' button. Clicking it sends CapturePayment to Worldline, settling the payment. The status changes from Authorised to Captured.")
    pdf.sub("Order Journey Viewer")
    pdf.txt("Click the 'Journey' button on any order to see a visual timeline of the entire payment flow. Each step shows:")
    pdf.bullet("Whether it was executed by the merchant app, the Worldline API, or the customer's browser")
    pdf.bullet("Color-coded actor badges: blue for merchant, green for Worldline API, orange for browser")
    pdf.bullet("Expandable API request/response data for each API call step")
    pdf.sub("Feature Audit")
    pdf.txt("Click 'Feature Audit' in the Orders header to see a coverage analysis of which Worldline Direct API features are implemented in the demo vs which are available. Includes a donut chart and categorized feature list.")
    pdf.sub("Status Colors")
    pdf.bullet("Blue - Payment session created (statusCode 0)", "CREATED: ")
    pdf.bullet("Amber - Payment approved, funds reserved (statusCode 5)", "AUTHORISED: ")
    pdf.bullet("Green - Payment settled, funds will transfer (statusCode 9)", "CAPTURED: ")
    pdf.bullet("Red - Payment declined, cancelled, or error (statusCode 2, 75, 96)", "FAILED: ")

    # 6 - Customers
    pdf.add_page()
    pdf.section("6", "Customers (CRM) Tab")
    pdf.txt("A lightweight CRM for managing customer relationships. Customers can be linked to orders for tracking and reporting.")
    pdf.sub("Customer List")
    pdf.txt("Shows all customers as cards with name, company, order count, and lifetime spend. Use the search bar to filter by name, email, or company.")
    pdf.sub("Adding a Customer")
    pdf.num(1, "Click '+ Add Customer'")
    pdf.num(2, "Enter name (required), email, company, phone, address")
    pdf.num(3, "Click 'Add Customer'")
    pdf.sub("Customer Detail View")
    pdf.txt("Click any customer card to see their full profile:")
    pdf.bullet("Contact information (email, company, phone, address)")
    pdf.bullet("Order count and lifetime value")
    pdf.bullet("Notes section - add timestamped notes about the customer")
    pdf.bullet("Full order history with status and payment flow")
    pdf.sub("Notes")
    pdf.txt("Notes are useful for tracking interactions: 'VIP customer - always offer express checkout', 'Prefers invoice payment', 'Contacted about recurring billing', etc.")
    pdf.sub("Linking to Orders")
    pdf.txt("When checking out in the Explorer, select a customer from the dropdown. The order will be linked to that customer, and their order count/lifetime value updates automatically.")

    # 7 - Code
    pdf.add_page()
    pdf.section("7", "Code Tab")
    pdf.txt("View the actual application source code with educational annotations. Perfect for developers who want to understand how the Worldline Direct API integration works.")
    pdf.sub("File Selection")
    pdf.txt("Four files are available: app.py (backend), app.js (frontend), style.css (styling), index.html (template). Click any file tab to load it.")
    pdf.sub("Annotations")
    pdf.txt("Key lines are highlighted with a purple background. Click any highlighted line to reveal an explanation of what that code does and why it matters for the payment integration.")
    pdf.txt("Over 20 annotations cover: HMAC signing, API authentication, payment flows, status codes, security considerations, and architectural decisions.")
    pdf.sub("Line Highlighting")
    pdf.bullet("Purple background = annotated line (click for explanation)")
    pdf.bullet("Blue left border = API route/endpoint definition")
    pdf.bullet("Green left border = Worldline API interaction")
    pdf.sub("Edit Mode")
    pdf.txt("By default, code is read-only. To enable editing:")
    pdf.num(1, "Click 'Unlock Edit' button")
    pdf.num(2, "Enter the service password")
    pdf.num(3, "Code switches to an editable text area")
    pdf.num(4, "Click 'Save Changes' (re-confirms password)")
    pdf.warn("IMPORTANT", "Code editing is restricted to authorized service personnel. The password is not shared in this guide - contact your team lead. Python changes require a server restart.")

    # 8 - Config
    pdf.add_page()
    pdf.section("8", "Configuration Tab")
    pdf.txt("Set up your Worldline Direct API credentials to connect to the test (or production) environment.")
    pdf.sub("Required Fields")
    pdf.bullet("Your PSPID from the Merchant Portal", "Merchant ID (PSPID): ")
    pdf.bullet("API Key ID from Developer > Payment API", "API Key: ")
    pdf.bullet("Secret API Key (shown once, save immediately!)", "API Secret: ")
    pdf.sub("Environment")
    pdf.txt("Select Test (preprod) or Production from the Base URL dropdown. Always use Test for demos and development.")
    pdf.sub("Order Settings")
    pdf.txt("Below the main credentials, configure:")
    pdf.bullet("Text prefix for generated order IDs (default: WLOP)", "Order ID Prefix: ")
    pdf.bullet("Choose from: PREFIX-UUID, PREFIX-TIMESTAMP, PREFIX-SEQ, FLOW-PREFIX-UUID", "Order ID Pattern: ")
    pdf.bullet("Sent as references.descriptor to Worldline", "Default Description: ")
    pdf.sub("Connection Status")
    pdf.txt("The header shows a green 'Connected' badge when configured, or red 'Not configured' when credentials are missing. A yellow banner at the top also prompts setup.")
    pdf.warn("SESSION STORAGE", "Credentials are stored in your browser session cookie. They are NOT saved permanently on the server. You'll need to re-enter them after clearing cookies or restarting.")

    # 9 - Payment Flows
    pdf.add_page()
    pdf.section("9", "Payment Flows Explained")
    pdf.sub("Flow 1: Hosted Checkout")
    pdf.txt("The simplest Worldline integration. Recommended for most merchants.")
    pdf.ln(1)
    pdf.num(1, "CREATE: Merchant sends CreateHostedCheckout (POST /v2/{mid}/hostedcheckouts) with amount, currency, merchantReference, and returnUrl. Worldline returns hostedCheckoutId and redirectUrl.")
    pdf.num(2, "REDIRECT: Customer's browser opens the Worldline-hosted payment page. They see all enabled payment methods and enter card details. Card data stays on Worldline's PCI-certified servers.")
    pdf.num(3, "RETURN: After payment, customer is redirected back to the merchant's returnUrl.")
    pdf.num(4, "STATUS: Merchant calls GetHostedCheckoutStatus (GET /v2/{mid}/hostedcheckouts/{id}) to verify the result. Returns payment ID, statusCode, card details.")
    pdf.num(5, "CAPTURE: Merchant calls CapturePayment (POST /v2/{mid}/payments/{id}/capture) to settle. Authorization only reserved funds; capture triggers the money transfer.")
    pdf.ln(2)
    pdf.sub("Flow 2: Server-to-Server (S2S)")
    pdf.txt("More control for the merchant. Requires PCI compliance or Hosted Tokenization for card data.")
    pdf.ln(1)
    pdf.num(1, "CREATE: Merchant sends CreatePayment (POST /v2/{mid}/payments) with card token/details, amount, and 3DS redirect URL. Worldline processes authorization directly.")
    pdf.num(2, "3DS REDIRECT: If 3-D Secure is required, customer is redirected to the issuer bank for authentication using the redirectURL from merchantAction.")
    pdf.num(3, "RETURN: Customer returns to the merchant's return URL.")
    pdf.num(4, "STATUS: Merchant calls GetPaymentDetails (GET /v2/{mid}/payments/{id}) to retrieve the final status, statusCode, and authorization result.")
    pdf.num(5, "CAPTURE: Same as Hosted Checkout - CapturePayment settles the authorized amount.")
    pdf.ln(2)
    pdf.sub("Key Differences")
    pdf.txt("Hosted Checkout is simpler (single redirect, automatic payment method display). S2S gives more control (direct payment processing, 3DS handling). Both end with the same Capture call.")
    pdf.tip("EDUCATIONAL NOTE", "In the Developer View, Hosted Checkout calls show endpoint /hostedcheckouts and S2S calls show /payments. The Capture step is shared.")

    # 10 - HMAC Authentication
    pdf.add_page()
    pdf.section("10", "HMAC Authentication")
    pdf.txt("Unlike Saferpay (which uses HTTP Basic Auth), the Worldline Direct API uses HMAC-SHA256 signatures for every request. This is more secure as the API Secret never leaves your server.")
    pdf.sub("Step-by-Step")
    pdf.num(1, "Build the string-to-hash from: HTTP method, Content-Type (POST only), Date (RFC 1123), and resource path")
    pdf.num(2, "Compute HMAC-SHA256 of the string using your API Secret as the key")
    pdf.num(3, "Base64-encode the signature")
    pdf.num(4, "Set Authorization header: GCS v1HMAC:<API_Key>:<base64_signature>")
    pdf.sub("Python Implementation")
    pdf.code([
        "import hmac, hashlib, base64",
        "",
        "string_to_hash = f'{method}\\n{content_type}\\n{date}\\n{resource}\\n'",
        "sig = hmac.new(secret.encode(), string_to_hash.encode(), hashlib.sha256)",
        "signature = base64.b64encode(sig.digest()).decode()",
        "auth = f'GCS v1HMAC:{api_key}:{signature}'",
    ])
    pdf.sub("Important Notes")
    pdf.bullet("The Date header must be in RFC 1123 format (e.g., Mon, 01 Mar 2026 12:00:00 GMT)")
    pdf.bullet("POST requests include Content-Type in the signature; GET requests do not")
    pdf.bullet("The resource path includes /v2/{merchantId}/ (e.g., /v2/YourPSPID/hostedcheckouts)")
    pdf.bullet("The string-to-hash always ends with a trailing newline")
    pdf.tip("AUTOMATIC", "The WLOP Explorer app handles all HMAC signing automatically via the wlop_sign() and wlop_request() functions in app.py.")

    # 11 - API Reference
    pdf.add_page()
    pdf.section("11", "API Reference")
    pdf.txt("All internal API endpoints used by the application:")
    pdf.ln(2)
    endpoints = [
        ("POST /api/config", "Save API credentials to session"),
        ("GET /api/config/status", "Check if credentials are configured"),
        ("GET /api/products", "List all products"),
        ("POST /api/products", "Add/update a product"),
        ("DELETE /api/products/<id>", "Delete a product"),
        ("GET /api/customers", "List all customers with stats"),
        ("POST /api/customers", "Add/update a customer"),
        ("DELETE /api/customers/<id>", "Delete a customer"),
        ("POST /api/customers/<id>/notes", "Add a note to a customer"),
        ("GET /api/customers/<id>/orders", "Get customer's order history"),
        ("POST /api/hosted-checkout/create", "CreateHostedCheckout"),
        ("POST /api/hosted-checkout/status", "GetHostedCheckoutStatus"),
        ("POST /api/payment/create", "CreatePayment (S2S)"),
        ("POST /api/payment/status", "GetPaymentDetails"),
        ("POST /api/capture", "CapturePayment (shared)"),
        ("GET /api/transactions", "List all transactions"),
        ("GET /api/feature-audit", "Feature coverage analysis"),
        ("GET /api/orders/<id>/journey", "Order journey timeline"),
        ("GET /api/status-codes", "WLOP status code reference"),
        ("GET /api/code/<file>", "Get annotated source code"),
        ("POST /api/code/unlock", "Verify service password"),
    ]
    for ep, desc in endpoints:
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(*WL_RED)
        pdf.cell(60, 5.2, ep)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*WL_DARK)
        pdf.cell(0, 5.2, desc, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.3)

    # 12 - Status Codes
    pdf.add_page()
    pdf.section("12", "Status Codes")
    pdf.txt("The Worldline Direct API uses numeric status codes (unlike Saferpay's string-based statuses). Key codes:")
    pdf.ln(2)
    status_codes = [
        ("0", "CREATED", "Payment session created, customer hasn't acted yet"),
        ("2", "DECLINED", "Payment was rejected by the issuer or acquirer"),
        ("5", "AUTHORISED", "Payment approved, funds reserved on card"),
        ("6", "AUTH_CANCELLED", "Authorization was reversed/cancelled"),
        ("9", "CAPTURED", "Payment settled, funds will transfer to merchant"),
        ("46", "WAITING_AUTH", "Waiting for 3-D Secure authentication"),
        ("75", "CANCELLED_CUSTOMER", "Customer cancelled the payment"),
        ("91", "CAPTURE_PENDING", "Capture is being processed"),
        ("96", "CANCELLED", "Payment was cancelled"),
        ("99", "PROCESSING", "Payment is being processed"),
    ]
    for code, name, desc in status_codes:
        pdf.set_font("Courier", "B", 9)
        pdf.set_text_color(*WL_RED)
        pdf.cell(10, 5.5, code)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*WL_NAVY)
        pdf.cell(38, 5.5, name)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*WL_DARK)
        pdf.cell(0, 5.5, desc, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.3)
    pdf.ln(2)
    pdf.tip("TIP", "Status codes 5 (Authorised) and 9 (Captured) are the two 'happy path' statuses. Code 5 means you can capture; code 9 means money is settled.")

    # 13 - Test Cards
    pdf.page_check()
    pdf.section("13", "Test Card Numbers")
    for brand, num in [("Visa", "4012 0000 3333 0026"), ("Mastercard", "5399 9999 9999 9999"),
                        ("American Express", "3714 496353 98431")]:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*WL_DARK)
        pdf.cell(38, 5.5, f"  {brand}")
        pdf.set_font("Courier", "", 9.5)
        pdf.cell(0, 5.5, num, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.txt("Expiry: any future date (e.g. 12/2030)  |  CVC: any 3 digits")
    pdf.ln(2)
    pdf.sub("Worldline vs Saferpay Test Cards")
    pdf.txt("Note that Worldline Direct API (WLOP) uses different test card numbers than the Saferpay API. The cards listed above are specific to the Worldline preprod environment.")

    # 14 - Version History
    pdf.add_page()
    pdf.section("14", "Version History")
    pdf.version_entry("1.0.0", "March 2026", [
        "Initial release with Explorer split-view (Shopper + Developer)",
        "Hosted Checkout flow (CreateHostedCheckout, GetStatus, Capture)",
        "Server-to-Server flow (CreatePayment, GetPaymentDetails, Capture)",
        "HMAC-SHA256 authentication for all Worldline API requests",
        "Product catalog management (CRUD + icon picker)",
        "Customer CRM (contacts, notes, search, lifetime value)",
        "Order Journey Viewer with timeline (merchant vs API vs browser)",
        "Feature Audit with SVG donut chart and coverage analysis",
        "Code Viewer with 20+ educational annotations",
        "Password-protected code edit mode for service personnel",
        "Configurable Order ID patterns with 4 options",
        "Test card reference for Worldline preprod environment",
        "Railway deployment support (Procfile, runtime.txt)",
    ])
    pdf.sub("Roadmap")
    pdf.bullet("Cancel payment (POST /v2/{mid}/payments/{id}/cancel)")
    pdf.bullet("Refund payment (POST /v2/{mid}/payments/{id}/refund)")
    pdf.bullet("Hosted Tokenization Page (iframe card input)")
    pdf.bullet("Recurring/subscription payment demo")
    pdf.bullet("Pay-by-Link generation via Merchant Portal")
    pdf.bullet("Dynamic Currency Conversion (DCC)")
    pdf.bullet("Webhook/notification endpoint demo")
    pdf.bullet("Dashboard analytics with charts")
    pdf.bullet("Batch capture for multiple transactions")

    # Final page
    pdf.add_page()
    pdf.ln(25)
    pdf._draw_logo(60, pdf.get_y(), 1.2)
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_text_color(*WL_NAVY)
    pdf.cell(0, 11, "You're All Set!", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*WL_DARK)
    for i, step in enumerate([
        "Open the app and go to Config tab",
        "Enter your PSPID, API Key, and API Secret",
        "Switch to Explorer and add products to cart",
        "Choose Hosted Checkout or Server-to-Server at checkout",
        "Pay with a test card and watch the API flow",
        "Explore Orders, Journey, Customers, and Code tabs",
    ], 1):
        pdf.cell(0, 7.5, f"     {i}.  {step}", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*WL_RED)
    pdf.set_line_width(0.6)
    pdf.line(65, pdf.get_y(), 145, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*WL_GREY)
    pdf.cell(0, 6, f"WLOP Explorer v{VERSION}  |  Built for Worldline  |  {DATE}", align="C")

    pdf.output("WLOP_Explorer_User_Guide.pdf")
    print("  -> WLOP_Explorer_User_Guide.pdf")


if __name__ == "__main__":
    print("Generating Worldline WLOP Explorer guides...")
    build_deployment_guide()
    build_user_guide()
    print("Done!")
