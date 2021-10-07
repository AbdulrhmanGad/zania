from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Res Config Settings'

    enable_sms_integration = fields.Boolean(string='Enable Integration', config_parameter='base_setup.enable_sms_integration')
    user_name = fields.Char(string="User Name", config_parameter='base_setup.user_name')
    user_pass = fields.Char(string="Password", config_parameter='base_setup.user_pass')
    sender = fields.Char(string="sender", config_parameter='base_setup.sender')
    # mobile = fields.Char(string="mobile", config_parameter='base_setup.mobile')
    # message = fields.Char(string="message", config_parameter='base_setup.message')