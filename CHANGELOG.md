# Changelog - WLOP Explorer

## v2.0 (2026-03-14)

### Tab Restructure
- Consolidated 6 tabs into 3 main tabs: **Explorer**, **Merchant Admin**, **Dev**
- Merchant Admin contains sub-tabs: Items (product catalog), Customers (CRM), Orders (transactions & journey)
- Dev contains sub-tabs: Code (source viewer), Config (API credentials), Feature Audit

### Webshop Improvements
- Product cards in shopper view are now larger and more prominent with hover effects
- Customer section after cart: choose "New Customer" or "Select Existing" from CRM
- Full customer details form: Name, Email, Street Address, City, Postal Code, Country, Phone
- After order completion, webshop resets for next order (clears dev panel logs)

### Feature Audit (moved to Dev tab)
- Every non-implemented feature now shows **"How to enable"** with backoffice activation instructions
- Added **OmniChannel Integration** - bridge POS and e-commerce channels
- Added **MOTO Transactions** - mail/phone order processing
- Activation notes cover account configuration, Merchant Portal settings, and PCI requirements

### Technical
- Sub-tab navigation with automatic data loading on tab switch
- Old tab name mappings preserved for backward compatibility of internal calls

---

## v1.0 (2025-11)

### Initial Release
- WLOP Explorer Online Payments Demo
- Split-view: Shopper panel + Developer API debugger
- Hosted Checkout and Server-to-Server payment flows
- Product catalog management
- Customer CRM with notes and order history
- Order journey visualization
- Source code viewer with annotations
- Feature audit with API coverage tracking
- HMAC-SHA256 request signing for Worldline Direct API
