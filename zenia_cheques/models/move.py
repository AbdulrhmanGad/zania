# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    payment_cheque_id = fields.Many2one('account.payment')


class AccountMove(models.Model):
    _inherit = 'account.move'
    payment_cheque_id = fields.Many2one('account.payment')


