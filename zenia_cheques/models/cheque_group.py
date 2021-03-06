# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class AccountPaymentGroup(models.Model):
    _name = 'account.payment.group'

    @api.onchange('cheque_book')
    def change_cheque_book(self):
        self.cheque_cheque_id = self.env['cheque.cheque'].search([
            ('done', '=', False),
            ('book_id', '=', self.cheque_book.id),
        ], limit=1, order='id asc')

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
        return super(AccountPaymentGroup, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('account.payment.group') or ''
        return super(AccountPaymentGroup, self).create(vals)

    name = fields.Char('Group Name')
    type = fields.Selection(string='Type', selection=[('receivable', 'Receivable'), ('send', 'Send'), ])
    cheque_no = fields.Integer('رقم الشيك')
    cheques_no = fields.Integer("Number of Cheques", required=True)
    cheques_total = fields.Float("Total Amount", required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    cheque_bank_id = fields.Many2one('res.bank', string='Bank')
    bank_branch_id = fields.Many2one("res.bank.branch", string="Branches")
    journal_id = fields.Many2one('account.journal', string='Journal')
    date = fields.Date('Date', default=fields.Date.today())
    due_date = fields.Date('Due Date', default=fields.Date.today())
    ref = fields.Char('Ref')
    cheque_ids = fields.One2many(comodel_name='account.payment', inverse_name='cheque_group_id', )
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    amount_in_currency = fields.Float("Amount in Company Currency", compute='compute_amount_in_currency', digits=(16, 4), )
    cheque_book = fields.Many2one('cheque.book', string="Cheque Ledger")
    cheque_cheque_id = fields.Many2one('cheque.cheque', string="Cheque Number")
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
        total = month = 0
        cheque_no = self.cheque_no
        # cheque_cheque_ids = self.cheque_book.cheque_ids.filtered(lambda x: x.done is False)
        cheque_cheque_ids = self.env['cheque.cheque'].search([
            ('book_id', '=', self.cheque_book.id),
            ('id', '>=', self.cheque_cheque_id.id),
            ('done', '=', False),
        ],order='id asc')
        # print("cheque_cheque_ids >>>> ",cheque_cheque_ids)
        for i in range(count):
            # print(i,">>>>>>>>>>>>>>. ", cheque_cheque_ids[i].id, cheque_cheque_ids[i].name)
            month += 1
            payment = self.env['account.payment'].create({
                'partner_type': 'customer' if self.type == 'receivable' else 'supplier',
                'cheque_type': 'receivable' if self.type == 'receivable' else 'send',
                'name': '/',
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'cheque_bank_id': self.cheque_bank_id.id,
                'bank_branch_id': self.bank_branch_id.id,
                'date': self.date,
                'due_date': self.due_date + relativedelta(months=month),
                'ref': self.ref,
                'cheque_no': cheque_no,
                'amount': round(self.cheques_total / self.cheques_no, 2),
            })
            if self.type == 'send':
                if cheque_cheque_ids[i]:
                    payment.write({'cheque_cheque_id': cheque_cheque_ids[i].id})
                # payment.cheque_cheque_id.payment_id = self.id
            cheque_no += 1
            total += round(self.cheques_total / self.cheques_no, 2)
            payment_ids.append(payment.id)
        if (self.cheques_total - total) > 0:
            month += 1
            payment = self.env['account.payment'].create({
                'partner_type': 'customer' if self.type == 'receivable' else 'supplier',
                'cheque_type': 'receivable' if self.type == 'receivable' else 'send',
                'name': '/',
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'date': self.date,
                'due_date': self.due_date + relativedelta(months=month),
                'ref': self.ref,
                'cheque_no': cheque_no,
                'amount': self.cheques_total - total,
            })
            if self.type == 'send':
                if cheque_cheque_ids[i]:
                    payment.write({'cheque_cheque_id': cheque_cheque_ids[i].id})
                # payment.cheque_cheque_id.payment_id = self.id
            payment_ids.append(payment.id)
        self.cheque_ids = [(6, 0, payment_ids)]
        self.state = 'confirm'

    @api.depends('currency_id', 'cheques_total' )
    def compute_amount_in_currency(self):
        for rec in self:
            rec.amount_in_currency = 0
            if rec.currency_id and len(rec.currency_id.rate_ids.ids)>0:
                rec.amount_in_currency = 1 / rec.currency_id.rate_ids[0].rate * rec.cheques_total
