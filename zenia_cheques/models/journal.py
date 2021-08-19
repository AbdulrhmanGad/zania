# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    receive_cheque = fields.Boolean( string='Receive Cheque')
    cheque_under_collect = fields.Boolean( string='Cheque Under Collection')
    cheque_collection = fields.Boolean( string='Cheque Collection')
    cheque_required = fields.Boolean( string='Required')
    cheque_reject = fields.Boolean( string='Reject')
    cheque_return = fields.Boolean( string='Return')
    cheque_close = fields.Boolean( string='Close')
    send_cheque = fields.Boolean( string='Send Cheque')
    cancel_cheque = fields.Boolean( string='Cancel Cheque')
    vendor_cheque = fields.Boolean( string='Vendor Cheque')

