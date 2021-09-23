from odoo import models, fields, api


class ContractTemplate(models.Model):
    _name = 'contract.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    type = fields.Selection( string='Type',selection=[('owner', 'Owner'),('subcontractor', 'Subcontractor')], required=True)
    account1_id = fields.Many2one(comodel_name='account.account', string="revenue") # cost acount for sub counterpart accout for owner
    account2_id = fields.Many2one(comodel_name='account.account', string="counterpart") # partner Account	for sub  counterpart for owner
