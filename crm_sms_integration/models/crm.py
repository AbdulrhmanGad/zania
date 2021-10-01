from odoo import fields, models, api, _
import requests
from odoo.exceptions import ValidationError


class CRMLead(models.Model):
    _inherit = 'crm.lead'
    _description = 'CRM Lead'

    def send_mobile_sms(self):
        enable_sms_integration = self.env['ir.config_parameter'].sudo().get_param('base_setup.enable_sms_integration')
        user_name = self.env['ir.config_parameter'].sudo().get_param('base_setup.user_name')
        user_pass = self.env['ir.config_parameter'].sudo().get_param('base_setup.user_pass')
        sender = self.env['ir.config_parameter'].sudo().get_param('base_setup.sender')
        mobile = self.env['ir.config_parameter'].sudo().get_param('base_setup.mobile')
        message = self.env['ir.config_parameter'].sudo().get_param('base_setup.message')
        print(">>>>>>>>>>> ", mobile)
        print(">>>>>>>>>>> ", type(mobile))
        if enable_sms_integration == 'True':
            if not user_name:
                raise ValidationError(_("Enter USER Name in SMS Integration settings"))
            if not user_pass:
                raise ValidationError(_("Enter Password in SMS Integration settings"))
            if not sender:
                raise ValidationError(_("Enter Sender in SMS Integration settings"))
            if mobile == False:
                raise ValidationError(_("Enter Mobile in SMS Integration settings"))
            if not message:
                raise ValidationError(_("Enter Message in SMS Integration settings"))
            url = "http://triple-core.ps/sendbulksms.php?user_name="+user_name+"&user_pass="+user_pass+"&sender="+sender+"&mobile="+mobile+"&type=0&text="+message
            print(">>>>>>>>>>>> URL", url)
            res = requests.post(url=url)
            print(">>>>>>>>>>>>>res", res)
            print(">>>>>>>>>>>>>res", res.content)

