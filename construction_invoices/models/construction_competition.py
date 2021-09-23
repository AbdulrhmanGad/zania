from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ConstructionCompetition(models.Model):
    _name = 'construction.competition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        super(ConstructionCompetition, self).name_search()
        args = args or []
        domain = []
        if name:
            domain = ['|',('project_id', operator, name), ('subcontractor_id', operator, name)]
        results = self.search(domain + args, limit=limit)
        return results.name_get()

    @api.depends('project_id', 'subcontractor_id')
    def name_get(self):
        result = []
        for rec in self:
            name = ('%s - %s' % (rec.project_id.name, rec.subcontractor_id.name))
            result.append((rec.id, name))
        return result

    project_id = fields.Many2one('construction.project2', required=True)
    date = fields.Date("Date")
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    subcontractor_id = fields.Many2one('res.partner', string='Subcontractor', required=True)
    line_ids = fields.One2many(comodel_name='construction.competition.line', inverse_name='competition_id' )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirm'), ],
        required=False, default='draft')
    technical_reason = fields.Text('Technical Reason')
    financial_reason = fields.Text('Financial Reason')

    @api.onchange('project_id')
    def change_project_id(self):
        self.customer_id = self.project_id.partner_id.id

    def confirm(self):
        self.state = 'confirm'

    def reset_draft(self):
        self.state = 'draft'


class ConstructionCompetitionLine(models.Model):
    _name = 'construction.competition.line'
    competition_id = fields.Many2one('construction.competition')
    item_id = fields.Many2one('tender.line', required=True) #, doamin=[('construction_id', '=', competition_id.project_id.id)]
    qty = fields.Float('Qty')
    unit_price = fields.Float('Unit Price')
    total = fields.Float('Total', compute='compute_total')

    @api.depends('unit_price', 'qty')
    def compute_total(self):
        for rec in self:
            rec.total = rec.unit_price * rec.qty

    @api.onchange('item_id')
    def change_item_id_price(self):
        for line in self.competition_id.project_id.tender_line_ids:
            if line.id == self.item_id.id:
                self.qty = line.qty

    @api.onchange('item_id')
    def change_item_id(self):
        if not self.competition_id.project_id:
            raise ValidationError(_("Please Select Project First !! "))
        if self.competition_id.project_id:
            res = {}
            lines = []
            for line in self.competition_id.project_id.tender_line_ids:
                lines.append(line.id)
            if len(lines) > 0:
                res['domain'] = {'item_id': [('id', 'in', lines)]}
            else:
                res['domain'] = {'item_id': [('id', 'in', False)]}
            return res
