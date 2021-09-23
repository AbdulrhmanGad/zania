# -*- coding: utf-8 -*-
{
    'name': "construction_invoices Version14 ",
    'summary': """ construction_invoices Version14 """,
    'description': """ "Construction Invoices Version14 """,
    'version': '12.0.2.0',
    'category': 'construction',
    'license': 'AGPL-3',
    'author': "",
    'website': '',
    'depends': ['base', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/menu.xml',
        'views/construction_project.xml',
        'views/construction_competition.xml',
        'views/construction_project_type.xml',
        'views/contract.xml',
        'views/invoices.xml',
        'views/contract_template.xml',
        'views/deduction_addition_view.xml',
        'views/financial.xml',
        'views/payment.xml',
        'views/project_charter.xml',
        'views/settings.xml',
        'views/wbs.xml',
        'views/wbs_distribution.xml',
        'views/wbs_distribution_auto.xml',
        'views/breakdown.xml',
        'report/construction_competition.xml',
        'report/project.xml',
        'report/financial.xml',
        'report/project_charter.xml',
    ],
}
