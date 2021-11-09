# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.osv import osv
import json

class RingdeskCallLogs(models.Model):
    _name = "ringdesk.calldetails"
    _description = "Call Details"
    _order = 'id DESC'
    _rec_name = 'call_id'

    parent_type = fields.Selection(selection=[('Lead', 'LEAD'), ('Contact', 'CONTACT')],string="Parent Type")
    parent_id = fields.Char('Parent ID')
    call_id = fields.Char('Call ID', required=True)
    from_name = fields.Char("From")
    to_name = fields.Char("To")
    phone = fields.Char("Phone Number")
    phone_status = fields.Selection(selection=[('INBOUND', 'Incoming'), ('OUTBOUND', 'Outgoing')],string="Status")
    call_start_time = fields.Datetime("Start Time", required=True)
    call_duration = fields.Char("Call Duration") # make compute function
    peer_name = fields.Char("Peer Name")
    notes = fields.Text("Notes")
    call_end_time = fields.Datetime("Call End Time")

    @api.model
    def create_contact(self, *args):
        record_set =()
        for arg in args:
            record_set = self.browse(arg[0])
        length = len(record_set)
        if length == 1:
            if record_set.parent_type :
                raise osv.except_osv(_('Forbbiden to create Contact'), _('Something got wrong!! Cannot create contact'))
            else:
               parent = self.env["res.partner"].create({'name': record_set.peer_name if record_set.peer_name != '' else record_set.phone, 'phone': record_set.phone})
               record_set.write({'parent_type': 'Contact', 'parent_id': parent.id})
               return {
                    'type': 'ir.actions.act_window',
                    'views': [[False,"form"]],
                    'res_id': parent.id,
                    'res_model': 'res.partner',
                    'target': 'new',
                }
       
    @api.model
    def create_lead(self, *args):
        lead_enable = self.env.user.has_group('crm.group_use_lead')
        if lead_enable:
            record_set = ()
            for arg in args:
                record_set = self.browse(arg[0])
            length = len(record_set)
            if length == 1:
                if record_set.parent_type == 'Contact':
                    parent = self.env["crm.lead"].create({'name': record_set.peer_name if record_set.peer_name != '' else record_set.phone, 'phone': record_set.phone})
                    record_set.write({'parent_type': 'Lead', 'parent_id': parent.id})
                    return {
                            'name': 'crm.lead.form',
                            'type': 'ir.actions.act_window',
                            'views': [[False,"form"]],
                            'res_id': parent.id,
                            'res_model': 'crm.lead',
                            'target': 'new',
                        }
                else:
                    raise osv.except_osv(_('Forbbiden to create Lead'), _('Something got wrong!! Cannot create Lead'))
        else:
            raise osv.except_osv(_('Forbbiden to create Lead'), _('Leads are not enable from CRM'))

   
    @api.model
    def copy(self, cr, default=None, context=None):
        raise osv.except_osv(_('Forbbiden to duplicate'), _('Is not possible to duplicate the record, please create a new one.'))

    @api.model
    def unlink(self, cr, default=None, context=None):
        raise osv.except_osv(_('Forbbiden to delete'), _('Is not possible to delete the record, please edit to make changes'))

            


        
