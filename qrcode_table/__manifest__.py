# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    "name": "POS Scan Table QR Code (Restaurant)",
    "version": "16.0.2.9",
    "category": "Point of Sale",
    "depends": ['pos_restaurant', 'website'],
    'license': 'OPL-1',
    'website': 'https://www.kanakinfosystems.com',
    'author': 'Kanak Infosystems LLP.',
    'summary': 'This module is very useful for restaurant owners who want to automate food ordering at the convenience of customer sitting at a particular table. | Table Booking | Table QR Code | QRCODE | QR Code | Table QR Code | POS Table QR Code',
    "description": "Order from your table by scanning QR Code using your mobile.",
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/template.xml',
        'views/modal_templates.xml',
        'views/website_confirm_order_templates.xml',
        'views/pos_config_view.xml',
    ],
    'images': [
        'static/description/banner.gif',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    "auto_install": False,
    'assets': {
        'web.assets_frontend': [
            'qrcode_table/static/src/css/quickview.css',
            'qrcode_table/static/src/css/custom.css',
            'qrcode_table/static/src/js/custom.js',
            'qrcode_table/static/src/js/theme.js',
        ],
        'point_of_sale.assets': [
            'qrcode_table/static/src/css/pos.css',
            'qrcode_table/static/lib/noty/lib/noty.css',
            'qrcode_table/static/lib/noty/lib/themes/light.css',
            'qrcode_table/static/src/js/models.js',
            'qrcode_table/static/lib/noty/lib/noty.js',
            'qrcode_table/static/src/js/Chrome.js',
            'qrcode_table/static/src/js/Screens/ProductScreen/TableOrderList.js',
            'qrcode_table/static/src/js/Screens/ProductScreen/TableOrderLine.js',
            'qrcode_table/static/src/js/Screens/ProductScreen/TableOrderPosLines.js',
            'qrcode_table/static/src/js/Screens/ProductScreen/ControlButtons/TableOrderButton.js',
            'qrcode_table/static/src/js/Screens/FloorScreen/FloorScreenExtended.js',
            'qrcode_table/static/src/xml/OrderReceipt.xml',
            'qrcode_table/static/src/xml/Screens/ProductScreen/ControlButtons/TableOrderButton.xml',
            'qrcode_table/static/src/xml/Screens/ProductScreen/TableOrderList.xml',
            'qrcode_table/static/src/xml/Screens/ProductScreen/TableOrderLine.xml',
            'qrcode_table/static/src/xml/Screens/ProductScreen/TableOrderPosLines.xml'
        ],
    },
    "installable": True,
    "price": 180,
    "currency": "EUR",
    'live_test_url': 'https://youtu.be/iLlgLMxYdAc',
}
