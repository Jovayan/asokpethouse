# -*- coding: utf-8 -*-
{
    'name': "Website Booking in odoo, Website Appointment Booking in odoo, calendar slot booking in odoo",
    'summary': "Website Appointment Booking in odoo,Website Booking in odoo, Website appointments doctor appointments book appointment clinic appointment calendar booking consultant booking online booking",
    'description': """
       Website Booking in odoo 16, 15, 14, 13, 12, Website Appointment Booking in odoo Website Booking, slot booking consultant booking online booking book appointment """,
    'category': 'website',
    'version': '16.0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','calendar','account','crm','contacts',
                'website','website_sale', 'hr'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/website_calendar_data.xml',
        # 'views/assets.xml',
	'views/res_config_view.xml',
        'views/portal_templates_view.xml',
        'views/portal_appointment_templates.xml',
        'views/appointment_views.xml',
        'views/menu_dashboard_view.xml',
        'views/website.xml',
        'views/website_view.xml',
        'views/appointment_source_views.xml',
        'views/appointee_views.xml',
        'views/appointment_group_views.xml',
        'views/appointment_timeslot_views.xml',
        'views/calendar_appointment_views.xml',
    ],
    # 'qweb': ["static/src/xml/appointment_dashboard.xml",
    #          ],
    'assets': {
        'web._assets_primary_variables': [
            '/website_booking_axis/static/src/css/custom_style.css',
        ],
        'web.assets_backend': [
            'website_booking_axis/static/src/xml/**/*',
            '/website_booking_axis/static/src/js/appointment_dashboard.js',
            '/website_booking_axis/static/src/js/jquery.dataTables.min.js',
            '/website_booking_axis/static/src/js/datatables.min.js',
            '/website_booking_axis/static/src/js/dataTables.buttons.min.js',
            '/website_booking_axis/static/src/js/Chart.js',
            '/website_booking_axis/static/src/css/nv.d3.css',
            '/website_booking_axis/static/src/scss/style.scss',

        ],
        'web.assets_frontend': [
            '/website_booking_axis/static/src/css/custom_style.css',
            '/website_booking_axis/static/src/js/custom_step_wizard.js',
            '/website_booking_axis/static/src/js/custom.js',

        ],

    },

    'price': 199.00,
    'currency': 'USD',
    'support': 'business@axistechnolabs.com',
    'author': 'Axis Technolabs',
    'website': 'https://www.axistechnolabs.com',
    'installable': True,
    'license': 'OPL-1',
    'images': ['static/description/images/banner.jpg'],

}
