# -*- coding: utf-8 -*-
{
    'name': 'Deferred Checks Process',
    'summary': 'A complete workflow and report for deferred checks',
    'description': """
    Note: checkboxes and rejected checks and Cash box have unique code format -> CB{Number} , RC{Number},CH{Number} 
    """,
    'author': 'Cybrosys Techno Solutions',
    'version': '10.0.1.0.0',
    'category': 'Accounting',
    'website': 'www.cybrosys.com',
    'depends': ['base', 'account', 'payment', 'account_check_printing', 'report_xlsx', ],
    'data': [
        'security/ir.model.access.csv',
        'reports/check_reports.xml',
        'views/records.xml',
        'views/payment_form_inherit.xml',
        'views/check_payment_view.xml',
        'views/wizard_view.xml',
        'views/due_date_wizard_view.xml',
        'views/defered_check_report.xml',
        'wizard/transfer_check_view.xml',
        'views/check_operation.xml',
        'views/check_search.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
}
