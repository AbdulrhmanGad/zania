# -*- coding: utf-8 -*-
{
    "name": "crm_sms_integration",
    "summary": "Zenia CRM SMS Integration",
    "category": "Website",
    "version": "14.0.0.1",
    "sequence": 1,
    "author": "Zenia",
    "website": "",
    "description": """ CRM SMS Integration """,
    "depends": ['crm'],
    "data": [
        'security/ir.model.access.csv',
        'views/crm_sms.xml',
        'views/settings.xml',
    ],
    "installable": True,
}
