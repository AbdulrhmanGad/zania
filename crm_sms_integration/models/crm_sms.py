from odoo import fields, models, api, _
import requests
from odoo.exceptions import ValidationError


class CRMSms(models.Model):
    _name = 'crm.sms'
    _description = 'CRM SMS'

    mobile = fields.Char(string='Mobile')
    name = fields.Text(string='Message', size=70)
    state = fields.Selection(string='State', selection=[('draft', 'Draft'), ('send', 'Send'), ],required=False, default='draft')

    def unlink(self):
        for rec in self:
            print(rec.state)
            if rec.state == 'send':
                raise ValidationError(_("You can not Delete Sent Message !!"))
        return super(CRMSms, self).unlink()

    @api.constrains('name')
    def _check_name(self):
        if len(self.name) > 70:
            raise ValidationError('Number of characters must not exceed 70')

    def send_mobile_sms(self):
        enable_sms_integration = self.env['ir.config_parameter'].sudo().get_param('base_setup.enable_sms_integration')
        user_name = self.env['ir.config_parameter'].sudo().get_param('base_setup.user_name')
        user_pass = self.env['ir.config_parameter'].sudo().get_param('base_setup.user_pass')
        sender = self.env['ir.config_parameter'].sudo().get_param('base_setup.sender')
        mobile = self.mobile
        message = self.name

        if enable_sms_integration == 'True':
            if not user_name:
                raise ValidationError(_("Enter USER Name in SMS Integration settings"))
            if not user_pass:
                raise ValidationError(_("Enter Password in SMS Integration settings"))
            if not sender:
                raise ValidationError(_("Enter Sender in SMS Integration settings"))
            # if mobile == False:
            #     raise ValidationError(_("Enter Mobile in SMS Integration settings"))
            # if not message:
            #     raise ValidationError(_("Enter Message in SMS Integration settings"))
            url = "http://triple-core.ps/sendbulksms.php?user_name="+user_name+"&user_pass="+user_pass+"&sender="+sender+"&mobile="+mobile+"&type=0&text="+message
            res = requests.post(url=url)
            if int(res.content) == 1001:
                self.state = 'send'

