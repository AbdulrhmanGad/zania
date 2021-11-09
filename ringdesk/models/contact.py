from odoo import models, fields, api


class remove_spaces_from_numbers(models.Model):
    _inherit = "res.partner"

    @api.onchange("phone")
    def remove_spaces_from_phone_number(self):
        for record in self:
            if record.phone:
                record.phone = record.phone.replace(" ", "")

    @api.onchange("mobile")
    def remove_spaces_from_mobile_number(self):
        for record in self:
            if record.mobile:
                record.mobile = record.mobile.replace(" ", "")
    
    @api.model
    def remove_space_old_data(self, *args):
        contacts = env['res.partner'].search([])
        for contact in contacts:
            contact.write({
            'lang': 'en_GB'
            })
        


