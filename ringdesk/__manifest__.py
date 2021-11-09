# -*- coding: utf-8 -*-
{
    'name': 'Phone integration for Swyx, 3CX, Xelion, BroadSoft',
    "summary": "Integrate your Swyx, 3CX, Xelion, BroadSoft and many more with in your ODOO crm",
    'version': '1.1',
    'category': 'web',
    "description": """
        This modules helps you to have telephony in ODOO, add Call Details in ODOO and attach to related contact or leads
    """,
    'author': 'Ringdesk B.V.',
    'maintainer': 'Ringdesk B.V.',
    'website': 'https://ringdesk.com',
    'depends': [
        'base', 
        'web',
        'contacts',
        'crm'
    ],
    'data': [
        'views/template.xml',
        'views/ringdesk_call_details.xml',
        'views/contact_lead_call_details_tab_view.xml',
        'views/ringdesk_settings.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.png'],
    'qweb': [
        'static/src/xml/*.xml',
    ], 
    'js': [
        'static/src/js/ringdesk_widget.js',
        'static/src/js/ringdesk_main.js',
        'static/src/js/ringdesk_init.js',
        'https://sdk.ringdesk.com/dist/ringdesk-kit.js'
    ],
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
