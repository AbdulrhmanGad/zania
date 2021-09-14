# -*- coding: utf-8 -*-
from odoo import models, fields, tools


class DifferedCheckHistory(models.Model):
    _name = "report.differed.check"
    _description = "Differed Check Analysis"
    _auto = False

    received_date = fields.Date(string='Received Date', store=True)
    payment_form = fields.Many2one('account.payment', string='Related Payment')
    name = fields.Char(string='Check')
    bank_account = fields.Many2one('res.bank', string='Bank Account')
    bank_name = fields.Char(string='Bank', related='bank_account.name', readonly=1, store=True)
    branch_name = fields.Char(string='Branch and Name')
    due_date = fields.Date(string='Due date')
    amount = fields.Float(string='Amount')
    state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('cancelled', 'Cancelled')], string='State')
    transfer_date = fields.Date(string='Transfer Date')
    issuer_name = fields.Many2one('res.partner', string='Issuer Name', required=1, store=True)
    deposit_date = fields.Date(string='Deposited Date')
    deposited_journal = fields.Many2one('account.journal', string='Deposited Journal')
    check_type = fields.Selection([('inbound', 'Received Check'),
                                   ('outbound', 'Issued Check'),
                                   ], string='Type of Check',
                                  )

    _order = 'name desc'

    def _select(self):
        select_str = """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.received_date as received_date,
                    t.payment_form as payment_form,
                    t.bank_account as bank_account,
                    t.bank_name as bank_name,
                    t.due_date as due_date,
                    t.branch_name as branch_name,
                    t.amount as amount,
                    t.name as name,

                    t.state as state,
                    t.transfer_date as transfer_date,
                    t.deposit_date as deposit_date,
                    t.deposited_journal as deposited_journal,
                    t.check_type as check_type
        """
        return select_str
#                      t.issuer_name as issuer_name,
    def _group_by(self):
        group_by_str = """
                GROUP BY
                    t.id,
                    received_date,
                    deposit_date,
                    payment_form,
                   
                    branch_name,
                    due_date,
                    bank_account,
                    bank_name,
                    check_type,
                    name,
                    state
        """
        return group_by_str
#      issuer_name,

    def init(self):
        tools.sql.drop_view_if_exists(self._cr, 'report_differed_check')
        self._cr.execute("""
            CREATE OR REPLACE view report_differed_check as
              %s
              FROM checks_paid t
                %s
        """ % (self._select(), self._group_by()))