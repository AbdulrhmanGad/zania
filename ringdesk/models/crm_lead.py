# -*- coding: utf-8 -*-

from odoo import api, models, fields
import json

class RingdeskCrmCallLogs(models.Model):
    _inherit = "crm.lead",
    call_logs = fields.One2many('ringdesk.calldetails', 'parent_id', string="Call Details",compute='_filtered_records')

    @api.model
    def _filtered_records(self):
        length = len(self._origin)
        if length == 1:
            domain=[('parent_type', '=', 'Lead'),('parent_id','=', self._origin.id)]
            related_recordset = self.env["ringdesk.calldetails"].search(domain)
            self.call_logs = related_recordset
        else:
            for record in self:
                domain=[('parent_type', '=', 'Lead'),('parent_id','=', record.id)]
                related_recordset = self.env["ringdesk.calldetails"].search(domain)
                record.call_logs = related_recordset
