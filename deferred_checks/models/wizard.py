# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime


class StockReport(models.TransientModel):
    _name = "wizard.check.report"
    _description = "Check Report"

    state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned')], string='State')
    date_from = fields.Date(string='From Date', required=1)
    date_to = fields.Date(string='To Date', default=datetime.today(), required=1)
    check_type = fields.Selection([('inbound', 'Received Check'),
                                   ('outbound', 'Issued Check'),
                                   ], string='Type of Check', required=1)

    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'checks.paid'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        # WWWWWWWWWWWWWWWWWWW
        print("XXXXXXXXXXXXXXX ", context.get('xls_export'))
        if context.get('xls_export'):
            print("XXXXXXSSSSSSSSSSSSSSSSSSSSS")
            vals = {
                'type': 'ir.actions.report',
                'report_name': 'deferred_checks.check_report_xls.xlsx',
                'datas': datas,
                'name': 'Check Report'
            }
            print(vals)

            return self.env["ir.actions.report"].search( [("report_name", "=", 'deferred_checks.check_report_xls.xlsx'), ("report_type", "=", 'xlsx')], limit=1, ).report_action(self, data=vals)
