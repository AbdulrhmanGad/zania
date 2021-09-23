from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    journal_id = fields.Many2one('account.journal', string="Owner Journal", config_parameter='base_setup.journal_id')
    sub_journal_id = fields.Many2one('account.journal', string="Subcontractor Journal", config_parameter='base_setup.sub_journal_id')
