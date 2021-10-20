# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResBankBranch(models.Model):
    _name = 'res.bank.branch'

    bank_id = fields.Many2one('res.bank', string="Bank", required=1)
    name = fields.Char('Name')
    branch_no = fields.Char('Branch No')
    Location = fields.Char('Location')


class ResBank(models.Model):
    _inherit = 'res.bank'

    branch_ids = fields.One2many( comodel_name='res.bank.branch',  inverse_name='bank_id', )
    branch_count = fields.Integer(compute='compute_branch_count')

    @api.depends('branch_ids')
    def compute_branch_count(self):
        for rec in self:
            rec.branch_count = len(rec.branch_ids.ids)

    def action_view_branches(self):
        action = self.env.ref("zenia_cheques.bank_branch_action").sudo().read()[0]
        action["domain"] = [("id", "in", self.branch_ids.ids)]
        return action