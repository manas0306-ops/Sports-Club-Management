{
    'name': 'The Champions Club - Sports Club Management System',
    'version': '17.0.1.0.0',
    'category': 'Services/Sports Club',
    'summary': 'Unified digital backbone for tennis, cricket, pro shop, bar tabs & member operations',
    'description': """
Sports Club Management System
=============================
Build the digital backbone of a club that has outgrown WhatsApp and Excel.

Features:
---------
* **Member Management (Scene 1)**: Gold, Silver, Junior tier tracking, expiry monitoring, quick member recognition & club history.
* **Court Scheduling & Collision Engine (Scene 2)**: 1-hour sessions, 30-min start intervals, strict anti-double-booking constraints, max 2 bookings/day per member, Friday night Social Play.
* **Unified Pro Shop & Inventory (Scene 3)**: Unified shelf stock between Counter POS and Online Sofa orders (Click & Collect/Delivery), auto member tier discounts.
* **Bar & Cafeteria POS (Scene 4)**: Table tracking, running tabs, kitchen order tickets (KOT), automatic discounts without asking, multi-payment (Cash, Card, UPI), end-of-day register closing.
* **Website Portal & CRM (Scene 5)**: Club website with live availability, trial session bookings, leads pipeline, quote dispatch, and 1-click member conversion.
* **Owner Financials & HR (Scene 6)**: Multi-channel consolidated revenue (Courts, Shop, Bar, Invoices), receivables, corporate billing, staff shifts, and leave approvals.
    """,
    'author': 'The Champions Club Team',
    'website': 'https://github.com/manas0306-ops/champions-club-odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'sale',
        'point_of_sale',
        'hr',
        'account'
    ],
    'data': [
        'security/sports_security.xml',
        'security/ir.model.access.csv',
        'data/sports_data.xml',
        'views/sports_menus.xml',
        'views/sports_member_views.xml',
        'views/sports_court_views.xml',
        'views/sports_shop_views.xml',
        'views/sports_bar_views.xml',
        'views/sports_crm_views.xml',
        'views/sports_finance_views.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
