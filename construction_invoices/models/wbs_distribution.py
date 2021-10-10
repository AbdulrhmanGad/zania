from PIL.ImageQt import qt_module
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class WbsDistribution(models.Model):
    _name = 'wbs.distribution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    project_id = fields.Many2one('construction.project2', 'project', required=1)
    partner_id = fields.Many2one('res.partner', 'Customer')
    line_ids = fields.One2many(comodel_name='wbs.distribution.line', inverse_name='wbs_distribution_id')

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.partner_id = self.project_id.partner_id.id

    @api.constrains('line_ids')
    def constrains_line_ids(self):
        for rec in self:
            for line in rec.line_ids:
                lines = rec.line_ids.filtered(lambda ln: ln.tender_id.id == line.tender_id.id)
                if line.tender_id.qty < sum(lnn.distribution_qty for lnn in lines):
                    raise ValidationError(_("for tender [%s] is greater than tender demanded [%s]") %(line.tender_id.name,line.tender_id.qty))


class WbsDistributionLine(models.Model):
    _name = 'wbs.distribution.line'

    wbs_distribution_id = fields.Many2one('wbs.distribution')
    tender_id = fields.Many2one('tender.line', 'Tender Item', required=True)
    tender_qty = fields.Float(related='tender_id.qty',string='Tender Qty')
    price_unit = fields.Float(string='Price Unit')
    total = fields.Float(string='Total', compute="compute_total")
    wbs_line_id = fields.Many2one('wbs.line',  string='WBS Item', )
    distribution_qty = fields.Float('Distribution Qty')
    start_date= fields.Date('Start Date')
    end_date= fields.Date('End Date')
    duration = fields.Integer(compute='compute_duration', string="Duration [Days]")

    @api.depends('price_unit', 'distribution_qty')
    def compute_total(self):
        for rec in self:
            rec.total = rec.distribution_qty * rec.price_unit

    @api.onchange('start_date', 'end_date')
    def change_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_('Start Date greater than End Date !!'))

    @api.depends('start_date', 'end_date')
    def compute_duration(self):
        for rec in self:
            rec.duration = 0
            if rec.end_date and rec.start_date:
                rec.duration = (rec.end_date - rec.start_date).days

    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        if not self.wbs_distribution_id.project_id:
            raise ValidationError(_('Please Select Project'))
        res = {}
        tender = []
        for line in self.wbs_distribution_id.project_id.tender_line_ids:
            tender.append(line.id)
        if len(tender) > 0:
            res['domain'] = {'tender_id': [('id', 'in', tender)]}
        else:
            res['domain'] = {'tender_id': [('id', 'in', False)]}
        return res

    @api.onchange('wbs_line_id', 'tender_id')
    def _onchange_wbs_line_id(self):
        res = {}
        items = []
        wbs = self.env['wbs'].search([
            ('project_id', "=", self.wbs_distribution_id.project_id.id),
            ('partner_id', "=", self.wbs_distribution_id.partner_id.id),
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

    @api.onchange('tender_id')
    def onchange_tender_id(self):
        self.tender_qty = self.tender_id.qty
