from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _name = 'contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'construction_project_id'

    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirm'), ],
        required=False, default='draft')
    contract_type = fields.Selection(
        string='Type',
        selection=[('1', 'Lump sum contract '),
                   ('2', 'Unit price contract'), ],
        required=True, default='1')
    competition_id = fields.Many2one('construction.competition', string='competition')
    date = fields.Date('Date', default=fields.Date.context_today, )
    attachment = fields.Binary("Attachment")

    def action_confirm(self):
        self.state = 'confirm'

    type = fields.Selection(string='Type', selection=[
        ('owner', 'Owner'),
        ('subcontractor', 'Subcontractor')
    ], required=True)
    name = fields.Char('Name',)
    construction_project_id = fields.Many2one(comodel_name='construction.project2', required=True, string="Project")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True,
                                 related="construction_project_id.partner_id")
    subcontractor_id = fields.Many2one('res.partner', string="Subcontractor", )
    contract_template_id = fields.Many2one(comodel_name='contract.template', required=True, string="Contract")
    account1_id = fields.Many2one(comodel_name='account.account', required=True,
                                  string="")  # cost account for sub counterpart accout for owner
    account2_id = fields.Many2one(comodel_name='account.account', required=True,
                                  string="")  # partner Account	for sub  counterpart for owner
    line_ids = fields.One2many(comodel_name='contract.line', inverse_name='contract_id')
    owner_line_ids = fields.One2many(comodel_name='contract.line', inverse_name='contract_id')
    addition_line_ids = fields.One2many(comodel_name='addition.line', inverse_name='contract_id', )
    deduction_line_ids = fields.One2many(comodel_name='deduction.line', inverse_name='contract_id', )
    total = fields.Float('Total', compute="compute_contract_lines_total")

    @api.model
    def create(self, vals):
        if 'type' in vals:
            print(vals)
            print(vals['type'])
            if vals['type'] == 'subcontractor':
                vals['name'] = self.env['ir.sequence'].next_by_code('sub.contract')
            elif vals['type'] == 'owner':
                vals['name'] = self.env['ir.sequence'].next_by_code('owner.contract')
        return super(Contract, self).create(vals)

    @api.onchange('construction_project_id')
    def _onchange_construction_project_id(self):
        if self.type == 'owner':
            lines = []
            for line in self.construction_project_id.tender_line_ids:
                line = self.env['contract.line'].create({
                    'product_id': line.id,
                    'name': line.name,
                    'description': line.description,
                    'quantity': line.qty,
                    'price_unit': line.price,
                    'note': line.note,
                })
                lines.append(line.id)
            print(lines)
            self.line_ids = [(6,0, lines)]

    @api.depends('line_ids.price_unit', 'line_ids.quantity')
    def compute_contract_lines_total(self):
        for rec in self:
            total = 0
            for line in rec.line_ids:
                total += line.total
            rec.total = total

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        super(Contract, self).name_search(name)
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', ('construction_project_id', '=ilike', name + '%'),
                      ('partner_id', operator, name),
                      ('partner_id', operator, name), ('subcontractor_id', operator, name), ]
        results = self.search(domain + args, limit=limit)
        return results.name_get()

    @api.depends('partner_id', 'construction_project_id')
    def name_get(self):
        result = []
        for rec in self:
            if rec.partner_id:
                name = ('%s - %s  %s' % (rec.construction_project_id.name, rec.partner_id.name,
                                         "-" + rec.subcontractor_id.name if rec.subcontractor_id else "",))
            else:
                name = ('%s ' % (rec.project_id.name))

            result.append((rec.id, name))
        return result

    @api.onchange('contract_template_id')
    def _onchange_contract_template(self):
        self.account2_id = self.contract_template_id.account2_id.id
        self.account1_id = self.contract_template_id.account1_id.id


class ContractLine(models.Model):
    _name = 'contract.line'
    contract_id = fields.Many2one(comodel_name='contract', string="Contract")
    type = fields.Selection(string='Type', related='contract_id.type')
    # product_id = fields.Many2one(comodel_name='product.product', string="Product", required=True)
    name = fields.Char('code', required=1)
    product_id = fields.Many2one(comodel_name='tender.line', string="Item", required=True)
    description = fields.Text('Description', required=True)
    uom_id = fields.Many2one('uom.uom')
    wbs_line_id = fields.Many2one(comodel_name='wbs.line', string="Wbs Item",)
    quantity = fields.Float('Quantity', required=True)
    price_unit = fields.Float('Price Unit', required=True, )
    total = fields.Float('Total', compute='compute_total')
    note = fields.Text('Note')

    @api.onchange('wbs_line_id')
    def change_wbs_line_id(self):
        if not self.contract_id.construction_project_id:
            raise ValidationError(_("Please Select Project "))
        if self.contract_id.construction_project_id:
            res = {}
            lines = []
            wbs_ids = self.env['wbs'].search([
                ('project_id', '=', self.contract_id.construction_project_id.id),
                ('partner_id', '=', self.contract_id.partner_id.id)
            ])
            for wbs in wbs_ids:
                for line in wbs.line_ids:
                    if line.type == 'child':
                        lines.append(line.id)
            if len(lines) > 0:
                res['domain'] = {'wbs_line_id': [('id', 'in', lines)]}
            else:
                res['domain'] = {'wbs_line_id': [('id', 'in', False)]}
            return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.contract_id.construction_project_id:
            raise ValidationError(_("Please Select Project "))
        if not self.contract_id.contract_type:
            raise ValidationError(_("Please Select Contract Type "))
        if self.contract_id.contract_type == '2' and not self.contract_id.competition_id:
            raise ValidationError(_("Please Select Competition "))
        if self.contract_id.contract_type == '2' and self.contract_id.competition_id:
            res = {}
            lines = []
            for line in self.contract_id.competition_id.line_ids:
                if self.product_id == line.item_id:
                    self.quantity = line.qty
                    self.price_unit = line.unit_price
                lines.append(line.item_id.id)
            print(self.contract_id.competition_id.line_ids)
            print(">>>>>>>>>>>", lines)
            if len(lines) > 0:
                res['domain'] = {'product_id': [('id', 'in', lines)]}
            else:
                res['domain'] = {'product_id': [('id', 'in', False)]}
            return res
        if self.contract_id.contract_type == '1':
            if self.contract_id.type == 'owner':
                res = {}
                lines = []
                for line in self.contract_id.construction_project_id.tender_line_ids:
                    lines.append(line.id)
                if len(lines)>0:
                    res['domain'] = {'product_id': [('id', 'in', lines)]}
                else:
                    res['domain'] = {'product_id': [('id', 'in', False)]}
                return res
            elif self.contract_id.type == 'subcontractor':
                res = {}
                lines = []
                wbs_distribution_ids =self.env['wbs.distribution'].search([
                    ('project_id', '=', self.contract_id.construction_project_id.id),
                    ('partner_id', '=', self.contract_id.partner_id.id),
                ])
                for wbs in wbs_distribution_ids:
                    for line in wbs.line_ids:
                        lines.append(line.tender_id.id)
                if len(lines) > 0:
                    res['domain'] = {'product_id': [('id', 'in', lines)]}
                else:
                    res['domain'] = {'product_id': [('id', 'in', False)]}
                return res

    @api.depends('price_unit', 'quantity')
    def compute_total(self):
        for rec in self:
            rec.total = rec.quantity * rec.price_unit


