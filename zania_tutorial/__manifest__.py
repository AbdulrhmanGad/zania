# -*- coding: utf-8 -*-
{
    'name': "zania_tutorial",
    'summary': """Zania Tutorial""",
    'description': """  """,
    'author': "Abdulrhman Mohammed",
    'website': "",
    'category': 'CRM',
    'version': '14.0.0.1',
    'depends': ['base', 'product', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}
