# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_book = fields.Many2one('cheque.book', string="Cheque Ledger")
    cheque_cheque_id = fields.Many2one('cheque.cheque', string="Cheque Number")

    @api.onchange('cheque_book', 'cheque_cheque_id')
    def change_cheque_book(self):
        res = {}
        lines = []
        for line in self.cheque_book.cheque_ids:
            lines.append(line.id)
        res['domain'] = {'cheque_cheque_id': [('id', 'in', lines)]}
        return res

    def cancel_cheque(self):
        if self.cheque_type == 'send':
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Send Cheque, " + self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_receivable_id.id,
                "name": self.partner_id.name,
                "ref": self.partner_id.name,
                "debit": 0,
                "credit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.journal_id.default_account_id.id,
                "name": self.journal_id.name,
                "ref": self.journal_id.name,
                "credit": 0,
                "debit": self.amount,
            })
            move_id.action_post()
            self.cheque_state = 'cancel'

    def confirm(self):
        if self.cheque_type == 'send':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Send Cheque, "+self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_payable_id.id,
                "name": self.partner_id.name,
                "ref": self.partner_id.name,
                "credit": 0,
                "debit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.journal_id.default_account_id.id,
                "name": self.journal_id.name,
                "ref": self.journal_id.name,
                "debit": 0,
                "credit": self.amount,
            })
            move_id.action_post()
            self.cheque_state = 'confirm'

    def collect(self):
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        if self.cheque_type == 'send':
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'date': self.collect_date,
                'journal_id': self.collect_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Collect " + self.name,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.journal_id.default_account_id.id,
                "name": self.journal_id.name,
                "ref": self.journal_id.name,
                "credit": 0,
                "debit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.collect_journal_id.default_account_id.id,
                "name": self.collect_journal_id.name,
                "ref": self.collect_journal_id.name,
                "debit": 0,
                "credit": self.amount,
            })
            move_id.action_post()
        self.cheque_state = 'collect'

    def reject_cheque(self):
        if self.cheque_type == 'send':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Reject Cheque, " + self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_receivable_id.id,
                "name": self.partner_id.name,
                "ref": self.partner_id.name,
                "debit": 0,
                "credit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.journal_id.default_account_id.id,
                "name": self.journal_id.name,
                "ref": self.journal_id.name,
                "credit": 0,
                "debit": self.amount,
            })
            move_id.action_post()
            self.cheque_state = 'confirm'
