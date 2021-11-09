# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID

class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

# user leads right of CRM
    @api.model
    def get_leads_activated(self):
        return self.env.user.has_group('crm.group_use_lead')
