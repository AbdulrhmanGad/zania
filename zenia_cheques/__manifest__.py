# -*- coding: utf-8 -*-

{
    'name': 'Zenia Cheques',
    'version': '14.0.1.0.0',
    'summary': 'Handle Receive and send Cheques',
    'author': 'Zenia',
    'company': 'Zenia', 
    'depends': ['base', 'account'],
    'category': 'Accounting',  
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/journal.xml',
        'views/cheque_book.xml',
        'views/receivable.xml',
        'views/send.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False, 
}

