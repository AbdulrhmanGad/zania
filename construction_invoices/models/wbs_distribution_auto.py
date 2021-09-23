from PIL.ImageQt import qt_module
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class WbsDistributionAuto(models.Model):
    _name = 'wbs.distribution.auto'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    project_id = fields.Many2one('construction.project2', 'project', required=1)
    partner_id = fields.Many2one('res.partner', 'Customer', required=1)
    wbs_id = fields.Many2one('wbs.distribution', 'Auto WBS',readonly=1 )
    tender_ids = fields.Many2many(comodel_name='tender.line', required=1)
    state = fields.Selection(string='State', selection=[('draft', 'Draft'), ('done', 'Done')], default='draft')

    line_ids = fields.One2many(
        comodel_name='wbs.distribution.auto.line',
        inverse_name='wbs_distribution_auto_id')

    def action_view_wbs(self):
        action = self.env.ref('construction_invoices.wbs_distribution_action').read()[0]
        action['domain'] = [('id', '=', self.wbs_id.id)]
        return action


    def create_wbs(self):
        if not self.tender_ids:
            raise  ValidationError(_("Please Enter Tender Lines"))
        if not self.line_ids:
            raise  ValidationError(_("Please Select WBS Lines"))
        wbs_id = self.env['wbs.distribution'].create({
            'project_id': self.project_id.id,
            'partner_id': self.partner_id.id,
        })
        for tender in self.tender_ids:
            for line in self.line_ids:
                self.env['wbs.distribution.line'].create({
                    'wbs_distribution_id': wbs_id.id,
                    'tender_id': tender.id,
                    'tender_qty': tender.qty,
                    'wbs_line_id': line.wbs_line_id.id,
                    'distribution_qty': tender.qty * line.percentage / 100,
                    'start_date': datetime.today().date(),
                })
        self.wbs_id = wbs_id.id
        self.state = 'done'

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.partner_id = self.project_id.partner_id.id


class WbsDistributionAutoLine(models.Model):
    _name = 'wbs.distribution.auto.line'

    wbs_distribution_auto_id = fields.Many2one('wbs.distribution.auto')
    wbs_line_id = fields.Many2one('wbs.line', 'WBS Item', required=1)
    percentage = fields.Float('Percentage %', required=1)

    @api.onchange('wbs_line_id', )
    def _onchange_wbs_line_id(self):
        res = {}
        items = []
        wbs = self.env['wbs'].search([
            ('project_id', "=", self.wbs_distribution_auto_id.project_id.id),
            ('partner_id', "=", self.wbs_distribution_auto_id.partner_id.id)
        ])
        for w in wbs:
            for line in w.line_ids:
                if line.type == 'child':
                    items.append(line.id)
        if len(items) > 0:
            res['domain'] = {'wbs_line_id': [('id', 'in', items)]}
        else:
            res['domain'] = {'wbs_line_id': [('id', 'in', False)]}
        return res
