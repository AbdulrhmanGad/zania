# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChequeCheque(models.Model):
    _name = 'cheque.cheque'
    book_id = fields.Many2one('cheque.book')
    payment_id = fields.Many2one('account.payment')
    name = fields.Char('Name')
    done = fields.Boolean('Done')


class ChequeBook(models.Model):
    _name = 'cheque.book'

    name = fields.Char('Book No')
    bank_id = fields.Many2one('res.bank', string="Bank", required=1)
    journal_id = fields.Many2one('account.journal', string="Journal")
    cheque_first_no = fields.Char('First No')
    cheque_numbers = fields.Integer('Cheque Numbers')
    cheque_no = fields.Char('Cheque No')
    cheque_ids = fields.One2many(comodel_name='cheque.cheque', inverse_name='book_id')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('cheque_created', 'Cheque Created'),
    ], required=True, default='draft')

    def generate_cheques(self):
        if not self.cheque_first_no.isdigit():
            raise ValidationError("Cheque Numbers Must be Only Digits")
        if not self.cheque_first_no:
            raise ValidationError("You Must Enter the First Cheque Number")
        if not self.cheque_numbers:
            raise ValidationError("You Must Enter The number OF Cheques")
        count = self.cheque_numbers
        for line in range(count):
            self.env['cheque.cheque'].create({
                'book_id': self.id,
                'name': int(self.cheque_first_no) + line,
            })
            count += 1
        self.state = 'cheque_created'
