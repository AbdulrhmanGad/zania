# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def get_default_journal(self):
        print("self.env.context ",self.env.context)
        print("self.env.context ",self._context)
        if 'default_cheque_type' in self.env.context:
            if self.env.context['default_cheque_type'] == 'receivable':
                return self.env['account.journal'].search([('receive_cheque', '=', True)])
            elif self.env.context['default_cheque_type'] == 'send':
                return self.env['account.journal'].search([('send_cheque', '=', True)])
        else:
            self._get_default_journal().id

    journal_id = fields.Many2one('account.journal', required=True,  string="Journal",default=get_default_journal)
    def unlink(self):
        for rec in self:
            if rec.cheque_state != 'draft':
                raise ValidationError(_("TO Delete cheque, State Must Be Draft !!"))
        return super(AccountPayment, self).unlink()

    cheque_group_id = fields.Many2one('account.payment.group')
    endorsement_partner_id = fields.Many2one('res.partner')
    endorsement_date = fields.Date('Endorsement Date')
    cheque_type = fields.Selection(
        string=' Cheque Type ',
        selection=[('receivable', 'Receivable'),
                   ('send', 'Send')])
    cheque_state = fields.Selection(
        string=' Cheque Status ',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirm'),
                   ('endorsement', 'Endorsement'),
                   ('received', 'Received'),
                   ('under_collect', 'Under Collect'),
                   ('collect', 'Collect'),
                   ('return', 'Returned'),
                   ('reject', 'Rejected'),
                   ('return_customer', 'Returned'),
                   ], default='draft', copy=False)
    cheque_no = fields.Integer('رقم الشيك')
    due_date = fields.Date('Due Date', required=True)
    cheque_bank_id = fields.Many2one("res.bank", string="Bank")
    move_ids = fields.One2many(comodel_name='account.move', inverse_name='payment_cheque_id')
    move_count = fields.Integer('Count', compute="compute_move_count")
    move_line_ids = fields.One2many(comodel_name='account.move.line', inverse_name='payment_cheque_id')
    move_line_count = fields.Integer('Count', compute="compute_move_count")

    under_collect_bank_id = fields.Many2one("res.bank", string="Bank")
    under_collect_journal_id = fields.Many2one("account.journal", string="Journal")
    under_collect_date = fields.Date(string='Date')

    collect_journal_id = fields.Many2one("account.journal", string="Collect Journal")
    collect_date = fields.Date(string='Collect Date')
    return_journal_id = fields.Many2one("account.journal", string="Return Journal")
    return_date = fields.Date(string='Return Date')

    return_journal_id = fields.Many2one("account.journal", string="Journal")
    return_date = fields.Date(string='Date')

    reject_journal_id = fields.Many2one("account.journal", string="Journal")
    reject_date = fields.Date(string='Date')
    current_journal_id = fields.Many2one("account.journal", string="Current Journal")

    # @api.onchange('journal_id')
    # def change_journal_id1(self):
    #     print("Journal")
    #     self.current_journal_id = self.journal_id.id
    #
    # @api.onchange('under_collect_journal_id')
    # def change_under_collect_journal_id(self):
    #     print("under_collect_journal_id")
    #     self.current_journal_id = self.under_collect_journal_id.id
    #
    # @api.onchange('collect_journal_id')
    # def change_collect_journal_id(self):
    #     print("collect_journal_id")
    #     self.current_journal_id = self.collect_journal_id.id
    #
    # @api.onchange('return_journal_id')
    # def change_return_journal_id(self):
    #     print("return_journal_id")
    #     self.current_journal_id = self.return_journal_id.id
    #
    # @api.onchange('reject_journal_id')
    # def change_reject_journal_id(self):
    #     print("reject_journal_id")
    #     self.current_journal_id = self.reject_journal_id.id

    @api.depends('move_ids')
    def compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids.ids)
            rec.move_line_count = len(rec.move_line_ids.ids)

    def action_view_moves(self):
        action = self.env.ref("zenia_cheques.action_move_journal_line_new").sudo().read()[0]
        action["domain"] = [("id", "in", self.move_ids.ids)]
        return action

    # @api.model
    # def create(self, values):
    #     res = super(AccountPayment, self).create(values)
    #     print("XXXXXXXXXXXXXXXXXXXX ", values)
    #     print("XXXXXXXXXXXXXXXXXXXX ", values['cheque_type'])
    #     if values['cheque_type'] in ['receivable', 'send']:
    #         print("XXXXXXXXXXXXXXXXXXXX ", values['cheque_type'])
    #
    #     if values['cheque_type']:
    #         payment_method = self.env['account.payment.method'].search([('code', '=', 'Checks')])
    #         print(">>>>>>>>>>>>>", payment_method)
    #         values['payment_method_id'] = payment_method.id
    #     return res
    #
    # def create(self, vals):
    #     print("XXXXXXXXXXXXXXXXXXXX ", vals)
    #     return super(AccountPayment, self).create(vals)

    def action_view_moves_lines(self):
        action = self.env.ref("account.action_account_moves_all").sudo().read()[0]
        action["domain"] = [("id", "in", self.move_line_ids.ids)]
        return action

    def reset_to_draft(self):
        if self.move_ids:
            raise ValidationError(_('Remove Move first to reset to draft'))
        self.cheque_state = 'draft'

    def confirm(self):
        if self.cheque_type == 'send':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': self.ref or "Send Cheque, " + self.name if self.name else ""
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
            self.move_id = move_id.id
            self.cheque_cheque_id.done = True
            self.cheque_state = 'confirm'
        if self.cheque_type == 'receivable':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': self.ref
            })
            print("<<<<<<<<<<<<<<<<<<<<< ", move_id)
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
            self.current_journal_id = self.journal_id.id
            move_id.action_post()
            self.move_id = move_id.id
            self.cheque_state = 'confirm'

    def return_to_customer(self):
        if self.cheque_type == 'send':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.return_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Return to Customer Cheque, " + self.name if self.name else ""
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_payable_id.id,
                "name": self.partner_id.name,
                "ref": self.partner_id.name,
                "debit": 0,
                "credit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.return_journal_id.default_account_id.id,
                "name": self.return_journal_id.name,
                "ref": self.return_journal_id.name,
                "credit": 0,
                "debit": self.amount,
            })
            move_id.action_post()
            self.move_id = move_id.id
            self.cheque_state = 'return_customer'
        if self.cheque_type == 'receivable':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.return_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Return to Customer Cheque, " + self.name if self.name else ""
            })
            print("<<<<<<<<<<<<<<<<<<<<< ", move_id)
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_receivable_id.id,
                "name": self.partner_id.name,
                "ref": self.partner_id.name,
                "credit": 0,
                "debit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.return_journal_id.default_account_id.id,
                "name": self.return_journal_id.name,
                "ref": self.return_journal_id.name,
                "debit": 0,
                "credit": self.amount,
            })
            self.current_journal_id = self.return_journal_id.id
            move_id.action_post()
            self.move_id = move_id.id
            self.cheque_state = 'return_customer'

    def open_under_collect(self):
        view_ref = self.env.ref('zenia_cheques.under_collect_view', False)
        return {
            'name': ('Under Collect Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }

    def open_collect(self):
        view_ref = self.env.ref('zenia_cheques.open_collect_view', False)
        return {
            'name': ('Collect Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }

    def open_endorsement(self):
        view_ref = self.env.ref('zenia_cheques.open_endorsement_view', False)
        return {
            'name': ('Endorsement Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }

    def under_collect(self):
        if self.cheque_type == 'receivable':
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'date': self.under_collect_date,
                'journal_id': self.under_collect_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Under Collect " + self.name,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.under_collect_journal_id.default_account_id.id,
                "name": self.under_collect_journal_id.name,
                "ref": self.under_collect_journal_id.name,
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
        self.current_journal_id = self.under_collect_journal_id.id
        self.cheque_state = 'under_collect'

    def collect(self):
        if self.cheque_type == 'receivable':
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
                "account_id": self.under_collect_journal_id.default_account_id.id or self.journal_id.default_account_id.id,
                "name": self.under_collect_journal_id.name,
                "ref": self.under_collect_journal_id.name,
                "debit": 0,
                "credit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.collect_journal_id.default_account_id.id,
                "name": self.collect_journal_id.name,
                "ref": self.collect_journal_id.name,
                "credit": 0,
                "debit": self.amount,
            })
            move_id.action_post()
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
        self.current_journal_id = self.collect_journal_id.id
        self.cheque_state = 'collect'

    def transfer(self):
        pass

    def open_return(self):
        view_ref = self.env.ref('zenia_cheques.open_return_view', False)
        return {
            'name': ('Return Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }

    def return_cheque(self):
        if self.cheque_type == 'receivable':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.return_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_receivable_id.id,
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
            self.cheque_state = 'return'
        self.current_journal_id = self.return_journal_id.id

    def open_reject(self):
        view_ref = self.env.ref('zenia_cheques.open_reject_view', False)
        return {
            'name': ('Reject Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }
    def open_return_to_customer(self):
        view_ref = self.env.ref('zenia_cheques.open_return_view', False)
        return {
            'name': ('Return Cheque'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
            'views': [(view_ref and view_ref.id or False, 'form')],
            'context': {}
        }

    def reject_cheque(self):
        if self.cheque_type == 'receivable':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.reject_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.reject_journal_id.default_account_id.id,
                "name": self.reject_journal_id.name,
                "ref": self.reject_journal_id.name,
                "credit": 0,
                "debit": self.amount,
                "partner_id": self.partner_id.id,
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.under_collect_journal_id.default_account_id.id or self.journal_id.default_account_id.id,
                "name": self.under_collect_journal_id.name,
                "ref": self.under_collect_journal_id.name,
                "debit": 0,
                "credit": self.amount,
            })
            move_id.action_post()
        if self.cheque_type == 'send':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.reject_journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': "Reject Cheque, " + self.name
            })
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                'payment_cheque_id': self.id,
                "account_id": self.partner_id.property_account_payable_id.id,
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
        self.current_journal_id = self.reject_journal_id.id
        self.cheque_state = 'reject'

    def endorsement_cheque(self):
        if self.cheque_type == 'receivable':
            if self.amount <= 0:
                raise ValidationError(_("Enter Positive Amount"))
            move_id = self.env['account.move'].create({
                'payment_cheque_id': self.id,
                'journal_id': self.journal_id.id,
                "partner_id": self.partner_id.id,
                'move_type': 'entry',
                'ref': self.name
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
            self.current_journal_id = self.journal_id.id
            move_id.action_post()
            self.move_id = move_id.id
            self.cheque_state = 'endorsement'
