# -*- coding: utf-8 -*-

from odoo import api, models, fields

class RingdeskSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ringdesk_oauth_enable = fields.Boolean(string="Enable Oauth 2.0", default=False)
    ringdesk_client_id = fields.Char(string="Client ID")
    ringdesk_client_secret = fields.Char(string= "Secret")

    @api.model
    def set_values(self):
        res = super(RingdeskSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('ringdesk.ringdesk_oauth_enable', self.ringdesk_oauth_enable)
        self.env['ir.config_parameter'].set_param('ringdesk.ringdesk_client_id', self.ringdesk_client_id)
        if self.ringdesk_client_secret != 'XXXXXXXXXXXXXXXXXXXX':
            self.env['ir.config_parameter'].set_param('ringdesk.ringdesk_client_secret', self.ringdesk_client_secret )
        return res

    @api.model
    def get_values(self):
        res = super(RingdeskSettings,self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        auth_enable = ICPSudo.get_param('ringdesk.ringdesk_oauth_enable')
        client_id = ICPSudo.get_param('ringdesk.ringdesk_client_id')
        client_secret = ICPSudo.get_param('ringdesk.ringdesk_client_secret')
        res.update(
            ringdesk_oauth_enable = auth_enable,
            ringdesk_client_id = client_id,
            ringdesk_client_secret = 'XXXXXXXXXXXXXXXXXXXX'
        )
        return res

    @api.model
    def get_auth_setting(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res = dict()
        res['ringdesk_client_id'] = ICPSudo.get_param('ringdesk.ringdesk_client_id')
        res ['ringdesk_client_secret'] =ICPSudo.get_param('ringdesk.ringdesk_client_secret')
        return res

    @api.model
    def is_oauth_enabled(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        return ICPSudo.get_param('ringdesk.ringdesk_oauth_enable')
        
    @api.model
    def remove_space_old_data(self, *args):
        contacts = self.env['res.partner'].search([])
        for contact in contacts:
            if contact.mobile:
                contact.write({'mobile':( contact.mobile.replace(' ', ''))});
            if contact.phone:
                contact.write({'phone': (contact.phone.replace(' ', ''))});
            