from odoo import models, fields, api


class Wbs(models.Model):
    _name = 'wbs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    project_id = fields.Many2one('construction.project2', 'project')
    partner_id = fields.Many2one('res.partner', 'Customer')
    line_ids = fields.One2many(comodel_name='wbs.line', inverse_name='wbs_id')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.partner_id = self.project_id.partner_id.id


class WbsLine(models.Model):
    _name = 'wbs.line'

    wbs_id = fields.Many2one('wbs')
    name = fields.Char('Name', required=1)
    code = fields.Char("Code")
    type = fields.Selection(
        string='Type',
        selection=[('parent', 'Parent'),
                   ('child', 'Child'), ],
        required=False, )

