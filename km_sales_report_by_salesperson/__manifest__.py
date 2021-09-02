{
    'name': 'Sales Report By Salesperson',
    'version': '14.0.0.0.1',
    'summary': 'Generate your sales order reports by salesperson, select multiple salesperson or single salesperson, print report from date and to date',
    'author': 'Kamrul Hasan',
    'maintainer': 'Kamrul Hasan',
    'Company': 'Tech Analyzers',
    'website': 'http://kamrul.net',
    'depends': ['base','sale_management'],
    'license': 'LGPL-3',
    'category': 'Sales',
    'data':[
        'wizards/sale_report_wizard.xml',
        'reports/sale_reports.xml',
        'reports/sale_report_view.xml',
    ],
    'images': ['static/description/sales_report_by_salesperson_banner.png'],
    'price': 0.0,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}