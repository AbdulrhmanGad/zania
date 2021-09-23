from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BreakDown(models.Model):
    _name = 'break.down'

    name = fields.Char(compute='compute_name')
    project_id = fields.Many2one('construction.project2')
    customer_id = fields.Many2one('res.partner', string='Customer')
    tender_line_id = fields.Many2one('tender.line')
    code = fields.Char('code')
    description = fields.Text('Description')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    item_id = fields.Many2one('construction.item', string='Item')
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure')
    qty = fields.Float('Quantity')
    type = fields.Selection(string='Type', selection=[('view', 'View'), ('transaction', 'Transaction')]
                            , default='view', required=True)
    note = fields.Text('Note')
    state = fields.Selection(string='State', selection=[
        ('draft', 'View'),
        ('confirm', 'Confirm'),
        ('approve', 'Approve'),
        ('financial', 'Financial Offer'),
    ], default='draft', required=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    differance = fields.Char('Differance', compute="compute_differance_date")
    line_ids = fields.One2many(comodel_name='break.down.line', inverse_name='break_down_id', )
    material_ids = fields.One2many(comodel_name='break.down.line', domain=[('type', '=', 'material')],
                                   inverse_name='break_down_id', )
    labour_ids = fields.One2many(comodel_name='break.down.line', domain=[('type', '=', 'labour')],
                                 inverse_name='break_down_id', )
    expenses_ids = fields.One2many(comodel_name='break.down.line', domain=[('type', '=', 'expenses')],
                                   inverse_name='break_down_id', )
    sub_contractor_ids = fields.One2many(comodel_name='break.down.line', domain=[('type', '=', 'sub_contractor')],
                                         inverse_name='break_down_id', )
    equipment_ids = fields.One2many(comodel_name='break.down.line', domain=[('type', '=', 'equipment')],
                                    inverse_name='break_down_id', )

    price_subtotal_material = fields.Float('Material', compute="compute_all_price_subtotal")
    price_subtotal_labour = fields.Float('labour', compute="compute_all_price_subtotal")
    price_subtotal_expenses = fields.Float('expenses', compute="compute_all_price_subtotal")
    price_subtotal_subcontractor = fields.Float('Sub Contractor', compute="compute_all_price_subtotal")
    price_subtotal_equipment = fields.Float('Equipment', compute="compute_all_price_subtotal")
    cost_price_total_all = fields.Float('Total', compute="compute_all_price_subtotal")

    total_value_material = fields.Float('Material', compute="compute_all_price_subtotal")
    total_value_labour = fields.Float('labour', compute="compute_all_price_subtotal")
    total_value_expenses = fields.Float('expenses', compute="compute_all_price_subtotal")
    total_value_subcontractor = fields.Float('Sub Contractor', compute="compute_all_price_subtotal")
    total_value_equipment = fields.Float('Equipment', compute="compute_all_price_subtotal")
    total_value_all = fields.Float('Total', compute="compute_all_price_subtotal")

    indirect_type = fields.Selection(string='Indirect Type',
                                     selection=[('percentage', 'Percentage'), ('amount', 'Amount')],
                                     default='amount')
    indirect_amount = fields.Float(string="Indirect Amount", store=1)
    indirect_percentage = fields.Float(string="Indirect Percentage", store=1)
    indirect_value = fields.Float(string="Indirect Value", compute='compute_indirect_amount')

    profit_type = fields.Selection(string='Profit Type', selection=[('percentage', 'Percentage'), ('amount', 'Amount')],
                                   default='amount')

    profit_amount = fields.Float(string="Profit Amount", store=1)
    profit_percentage = fields.Float(string="Profit Percentage", store=1)
    profit_value = fields.Float(string="Gross", compute='compute_profit_value')

    tax = fields.Float(string="Tax Percentage")
    tax_amount = fields.Float(string="Tax Amount", compute='compute_tax')

    sale_price_amount = fields.Float(string='Sale Price', compute='compute_sale_price')
    sale_price_amount_all = fields.Float(string="Total Sale", compute='compute_sale_price')

    @api.depends('qty', 'indirect_value', 'profit_amount', 'tax_amount')
    def compute_sale_price(self):
        for rec in self:
            rec.sale_price_amount = rec.indirect_value + rec.profit_amount + rec.tax_amount
            rec.sale_price_amount_all = rec.sale_price_amount * rec.qty


    def unlink(self):
        if self.state != 'draft':
            raise  ValidationError(_("Can not Delete Confirmed BreakDown"))
        return super(BreakDown, self).unlink()


    @api.depends('tax', 'profit_value')
    def compute_tax(self):
        for rec in self:
            rec.tax_amount = rec.tax / 100 * rec.profit_value


    @api.onchange('profit_amount')
    def _onchange_profit_amount(self):
        for rec in self:
            if rec.profit_type == 'amount':
                rec.profit_percentage = (rec.profit_amount / rec.indirect_value) * 100

    @api.onchange('profit_percentage')
    def _onchange_profit_percentage(self):
        for rec in self:
            if rec.profit_type == 'percentage':
                rec.profit_amount = rec.indirect_value * rec.profit_percentage / 100

    @api.onchange('profit_type', )
    def _onchange_profit_type(self):
        for rec in self:
            if rec.profit_type == 'amount':
                rec.profit_percentage = (rec.profit_amount / rec.indirect_value) * 100
            else:
                self.profit_amount = (rec.indirect_value * rec.profit_percentage) / 100

    @api.depends('profit_type', 'profit_percentage', 'profit_amount', 'indirect_value')
    def compute_profit_value(self):
        for rec in self:
            rec.profit_value = rec.indirect_value + (rec.indirect_value * rec.profit_percentage / 100) if rec.profit_type == 'percentage' else rec.profit_amount + rec.indirect_value


    @api.onchange('indirect_amount')
    def _onchange_indirect_amount(self):
        for rec in self:
            if rec.indirect_type == 'amount':
                rec.indirect_percentage = (rec.indirect_amount / rec.cost_price_total_all) * 100

    @api.onchange('indirect_percentage')
    def _onchange_indirect_percentage(self):
        for rec in self:
            if rec.indirect_type == 'percentage':
                rec.indirect_amount = rec.cost_price_total_all * rec.indirect_percentage / 100

    @api.onchange('indirect_type', )
    def _onchange_indirect_type(self):
        for rec in self:
            if rec.indirect_type == 'amount':
                rec.indirect_percentage = (rec.indirect_amount / rec.cost_price_total_all) * 100
            else:
                self.indirect_amount = (rec.cost_price_total_all * rec.indirect_percentage) / 100

    @api.depends('indirect_type', 'indirect_percentage', 'indirect_amount', 'cost_price_total_all')
    def compute_indirect_amount(self):
        for rec in self:
            rec.indirect_value = rec.cost_price_total_all + (
                        rec.cost_price_total_all * rec.indirect_percentage / 100) if rec.indirect_type == 'percentage' else rec.indirect_amount + rec.cost_price_total_all

    @api.depends('material_ids', 'labour_ids', 'expenses_ids', 'sub_contractor_ids', 'equipment_ids')
    def compute_all_price_subtotal(self):
        for rec in self:
            rec.price_subtotal_material = sum([x.price_cost_subtotal for x in rec.material_ids])
            rec.total_value_material = sum([x.price_cost_subtotal for x in rec.material_ids]) * rec.qty
            rec.price_subtotal_labour = sum([x.price_cost_subtotal for x in rec.labour_ids])
            rec.total_value_labour = sum([x.price_cost_subtotal for x in rec.labour_ids]) * rec.qty
            rec.price_subtotal_expenses = sum([x.price_cost_subtotal for x in rec.expenses_ids])
            rec.total_value_expenses = sum([x.price_cost_subtotal for x in rec.expenses_ids]) * rec.qty
            rec.price_subtotal_subcontractor = sum([x.price_cost_subtotal for x in rec.sub_contractor_ids])
            rec.total_value_subcontractor = sum([x.price_cost_subtotal for x in rec.sub_contractor_ids]) * rec.qty
            rec.price_subtotal_equipment = sum([x.price_cost_subtotal for x in rec.equipment_ids])
            rec.total_value_equipment = sum([x.price_cost_subtotal for x in rec.equipment_ids]) * rec.qty
            rec.cost_price_total_all = rec.price_subtotal_material + rec.price_subtotal_labour + rec.price_subtotal_expenses + rec.price_subtotal_subcontractor + rec.price_subtotal_equipment
            rec.total_value_all = rec.total_value_material + rec.total_value_labour + rec.total_value_expenses + rec.total_value_subcontractor + rec.total_value_equipment

    @api.depends('start_date', 'end_date')
    def compute_differance_date(self):
        for rec in self:
            rec.differance = ''
            if rec.start_date and rec.end_date:
                d1 = datetime.strptime(str(rec.start_date), "%Y-%m-%d")
                d2 = datetime.strptime(str(rec.end_date), "%Y-%m-%d")
                rec.differance = (d2 - d1).days + ' Days'

    @api.onchange('tender_line_id')
    def change_tender_line_id(self):
        self.code = self.tender_line_id.name
        self.description = self.tender_line_id.description

    @api.depends('project_id', 'tender_line_id', 'description')
    def compute_name(self):
        for rec in self:
            project = rec.project_id.name if rec.project_id else ''
            tender = ", " + rec.tender_line_id.name if rec.tender_line_id else ''
            description = ", " + rec.description if rec.description else ''
            rec.name = project + tender + description

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):
        self.state = 'approve'

    def action_financial(self):
        self.state = 'financial'


class BreakDownLine(models.Model):
    _name = 'break.down.line'

    type = fields.Selection(string='Type', selection=[
        ('material', 'Material'),
        ('labour', 'Labour'),
        ('expenses', 'Expenses'),
        ('sub_contractor', 'Sub Contractor'),
        ('equipment', 'Equipment'),
    ], required=False, )

    break_down_id = fields.Many2one('break.down')
    product_id = fields.Many2one('product.product', 'Product', required="1")
    description = fields.Text('Description')
    uom_id = fields.Many2one('uom.uom', 'Unit Of Measure')
    qty = fields.Float('Quantity')
    waste = fields.Float('Waste%')
    planed_qty = fields.Float('Planned Quantity', compute="compute_planned_qty", store=True)
    cost_per_unit = fields.Float('Cost / Unit')
    price_cost_subtotal = fields.Float('Price Cost Subtotal', compute="compute_price_cost_subtotal", store=True)
    total_qty = fields.Float('Total Quantity', compute='compute_total_qty', store=True)
    total_value = fields.Float('Total Value', compute="compute_total_value")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.depends('price_cost_subtotal', 'break_down_id.qty')
    def compute_total_value(self):
        for rec in self:
            rec.total_value = rec.price_cost_subtotal * rec.break_down_id.qty

    @api.depends('planed_qty', 'break_down_id.qty')
    def compute_total_qty(self):
        for rec in self:
            rec.total_qty = rec.planed_qty * rec.break_down_id.qty

    @api.depends('planed_qty', 'cost_per_unit')
    def compute_price_cost_subtotal(self):
        for rec in self:
            rec.price_cost_subtotal = rec.planed_qty * rec.cost_per_unit

    @api.depends('waste', 'qty')
    def compute_planned_qty(self):
        for rec in self:
            if rec.type == 'material':
                rec.planed_qty = rec.qty + (rec.qty * rec.waste) / 100
            else:
                rec.planed_qty = 1

    @api.onchange('product_id')
    def change_product_id(self):
        self.description = self.product_id.name
