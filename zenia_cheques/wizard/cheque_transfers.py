# -*- coding: utf-8 -*-
import logging
from odoo.tools.translate import _
from odoo.tools import email_split
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo import api, fields, models
import requests
import json


class ChequesTransfersWizard(models.TransientModel):
    _name = 'wizard.cheque.transfers'
    _description = 'Cheque Transfers Wizard'

    res_ids = fields.Many2many(comodel_name="account.payment", )
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
                   ], copy=False, compute="compute_cheque_state")
    cheque_type = fields.Selection(string=' Cheque Type ',
                                   selection=[('receivable', 'Receivable'), ('send', 'Send')], compute="compute_cheque_type")

    def get_default_journal(self):
        print("self.env.context ",self.env.context)
        print("self.env.context ",self._context)
        if 'default_cheque_type' in self.env.context:
            if self.env.context['default_cheque_type'] == 'receivable':
                return self.env['account.journal'].search([('receive_cheque', '=', True)])
            elif self.env.context['default_cheque_type'] == 'send':
                return self.env['account.journal'].search([('send_cheque', '=', True)])
        else:
            self.env['account.payment'].search([],limit=1)._get_default_journal().id
    journal_id = fields.Many2one('account.journal', required=True,  string="Journal",default=get_default_journal)
    current_journal_id = fields.Many2one("account.journal", string="Current Journal")

    under_collect_bank_id = fields.Many2one("res.bank", string="Bank")
    under_collect_journal_id = fields.Many2one("account.journal", string="Journal")
    under_collect_date = fields.Date(string='Date')

    collect_journal_id = fields.Many2one("account.journal", string="Collect Journal")
    collect_date = fields.Date(string='Collect Date')

    return_journal_id = fields.Many2one("account.journal", string="Return Journal")
    return_date = fields.Date(string='Return Date')

    reject_journal_id = fields.Many2one("account.journal", string="Journal")
    reject_date = fields.Date(string='Date')

    @api.depends('res_ids')
    def compute_cheque_type(self):
        for rec in self:
            rec.cheque_type = False
            if rec.res_ids:
                rec.cheque_type = rec.res_ids[0].cheque_type

    @api.depends('res_ids')
    def compute_cheque_state(self):
        for rec in self:
            rec.cheque_state = False
            if rec.res_ids:
                rec.cheque_state = rec.res_ids[0].cheque_state

    @api.onchange('res_ids')
    @api.constrains('res_ids')
    def _onchange_res_ids(self):
        for rec in self:
            cheque_state = rec.res_ids[0].cheque_state if rec.res_ids else False
            partner_id = rec.res_ids[0].partner_id if rec.res_ids else False
            for line in rec.res_ids:
                if line.partner_id != partner_id:
                    raise  ValidationError(_("All Selected Partner Must be the Same Partner"))
                if line.cheque_state != cheque_state:
                    raise  ValidationError(_("All Selected Cheque State Must be the Same state"))

    def confirm(self):
        for line in self.res_ids:
            line.confirm()

    def open_under_collect(self):
        for line in self.res_ids:
            line.open_under_collect()

    def open_collect(self):
        for line in self.res_ids:
            line.open_collect()

    def open_return(self):
        for line in self.res_ids:
            line.open_return()

    def open_endorsement(self):
        for line in self.res_ids:
            line.open_endorsement()

    def open_return_to_customer(self):
        for line in self.res_ids:
            line.open_return_to_customer()

    def open_reject(self):
        for line in self.res_ids:
            line.open_reject()

    def reset_to_draft(self):
        for line in self.res_ids:
            line.reset_to_draft()