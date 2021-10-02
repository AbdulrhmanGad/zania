# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_book = fields.Many2one('cheque.book', string="Cheque Ledger")
    cheque_cheque_id = fields.Many2one('cheque.cheque', string="Cheque Number")

    @api.onchange('cheque_book')
    def change_cheque_book(self):
        self.cheque_cheque_id = self.env['cheque.cheque'].search([
            ('done', '=', False),
            ('book_id', '=', self.cheque_book.id),
        ], limit=1, order='id asc')

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


