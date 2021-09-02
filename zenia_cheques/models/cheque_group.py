# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentGroup(models.Model):
    _name = 'account.payment.group'

    @api.onchange('cheque_ids', 'cheques_total')
    @api.constrains('cheque_ids', 'cheques_total')
    def change_cheque_ids(self):
        if self.state == 'confirm':
            total = 0
            for line in self.cheque_ids:
                total += line.amount
            if self.cheques_total != int(total):
                raise ValidationError(_("Group Total Amount is not Match With Line amounts"))

    def unlink(self):
        for line in self.cheque_ids:
            if line.cheque_state != 'draft':
                raise ValidationError(_('One or More Cheque Group line state must be draft'))
        for line in self.cheque_ids:
            line.unlink()
        # if self.cheque_ids:
        #     raise ValidationError(_('Delete All Payments First'))
        return  super(AccountPaymentGroup, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('account.payment.group') or ''
        return super(AccountPaymentGroup, self).create(vals)

    name = fields.Char('Group Name')
    cheques_no = fields.Integer("Cheques Numbers", required=True)
    cheques_total = fields.Float("Total Amount", required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    cheque_bank_id = fields.Many2one('res.bank', string='Bank')
    journal_id = fields.Many2one('account.journal', string='Journal')
    date = fields.Date('Date')
    ref = fields.Char('Ref')
    cheque_ids = fields.One2many(comodel_name='account.payment', inverse_name='cheque_group_id', )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection(
        string='Status ', selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirmed'),
            ('confirm_cheque', 'Confirm Cheques'),
        ], default='draft')

    def confirm_cheques(self):
        for line in self.cheque_ids:
            line.confirm()
        self.state = 'confirm_cheque'

    def reset_to_draft(self):
        for line in self.cheque_ids:
            line.reset_to_draft()
        self.state = 'draft'



    def confirm_group(self):
        if self.cheques_total <= 0:
            raise ValidationError(_('Enter Positive Amount'))
        payment_ids = []
        count = self.cheques_no
        total = 0
        for i in range(count):
            payment = self.env['account.payment'].create({
                'partner_type': 'customer',
                'cheque_type': 'receivable',
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'cheque_bank_id': self.cheque_bank_id.id,
                'date': self.date,
                'ref': self.ref,
                'amount': round(self.cheques_total / self.cheques_no, 2),
            })
            print(self.cheques_total / self.cheques_no)
            total += round(self.cheques_total / self.cheques_no, 2)
            payment_ids.append(payment.id)
            print(">>>>>>>>>>>>>>>>> ", payment)
        print(self.cheques_total, "==", total, "Differe>> ", self.cheques_total - total)
        if (self.cheques_total - total) > 0:
            payment = self.env['account.payment'].create({
                'partner_type': 'customer',
                'cheque_type': 'receivable',
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'date': self.date,
                'ref': self.ref,
                'amount': self.cheques_total - total,
            })
            payment_ids.append(payment.id)
        self.cheque_ids = [(6, 0, payment_ids)]
        self.state = 'confirm'

