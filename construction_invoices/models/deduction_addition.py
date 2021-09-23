from odoo import models, fields, api


class ConstructionDeduction(models.Model):
    _name = 'construction.deduction.addition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=1)
    account_id = fields.Many2one(comodel_name='account.account', required=1)
    type = fields.Selection(string='Type', selection=[
        ('addition', 'Addition'),
        ('deduction', 'Deduction')
    ], required=True)
    to = fields.Selection(string='To', selection=[('owner', 'Owner'), ('subcontractor', 'Subcontractor')],
                          required=True)
    percentage = fields.Boolean(string='Percentage')
    value = fields.Float('Value')
    down_payment = fields.Boolean(string='Down Payment')


class AdditionLine(models.Model):
    _name = 'addition.line'
    contract_id = fields.Many2one(comodel_name='contract')
    move_id = fields.Many2one(comodel_name='construction.invoice')
    contract_type = fields.Selection(string='Type', related='contract_id.type')
    name = fields.Many2one(comodel_name='construction.deduction.addition', required=True, )
    account_id = fields.Many2one(comodel_name='account.account', required=True, )
    percentage = fields.Boolean(string='%')
    percentage_amount = fields.Float(string='% Amount')
    last_value = fields.Float('Last Value')
    value = fields.Float('current Value', )
    contract_total_value = fields.Float('Total', compute="compute_contract_total")
    total = fields.Float('Total Value', compute="compute_total")
    total_value = fields.Float('Total', compute="compute_total")
    down_payment = fields.Boolean(string='Down Payment')

    @api.depends('percentage', 'percentage_amount','move_id.current_value')
    def compute_contract_total(self):
        for rec in self:
            rec.contract_total_value = rec.percentage_amount if rec.percentage is False else \
                rec.contract_id.total * rec.percentage_amount / 100

    @api.depends('total', 'percentage_amount', 'percentage', 'last_value')
    def compute_current(self):
        for rec in self:
            rec.value = (rec.move_id.current_value * rec.percentage_amount / 100) if rec.percentage is True else rec.total_value - rec.last_value

    @api.onchange('name')
    def onchange_name(self):
        self.account_id = self.name.account_id.id
        self.percentage = self.name.percentage
        self.percentage_amount = self.name.value
        self.value = self.percentage_amount if self.percentage is False else (self.value * self.percentage / 100)
        if self.move_id:
            res = {}
            lines = []
            addition_lines = self.env['construction.deduction.addition'].search([
                ('to', '=', self.move_id.contract_id.type),
                ('type', '=', 'addition'),
            ])
            # for line in self.move_id.contract_id.addition_line_ids:
            for line in addition_lines:
                # lines.append(line.name.id)
                lines.append(line.id)
            res['domain'] = {'name': [('id', 'in', lines)]}
            return res

    @api.onchange('percentage', 'percentage_amount')
    def change_percentage(self):
        for rec in self:
            rec.value = rec.total_value - rec.last_value

    @api.depends('last_value', 'percentage', 'percentage_amount','move_id.invoice_total')
    def compute_total(self):
        for rec in self:
            rec.total = 0
            total = 0
            if rec.percentage is True:
                for line in rec.move_id.invoice_line_ids:
                    total += line.total_value
                rec.total_value = (rec.move_id.invoice_total * rec.percentage_amount / 100)
            else:
                rec.total_value = rec.percentage_amount


class DeductionLine(models.Model):
    _name = 'deduction.line'
    contract_id = fields.Many2one(comodel_name='contract')
    move_id = fields.Many2one(comodel_name='construction.invoice')
    contract_type = fields.Selection(string='Type', related='contract_id.type')
    name = fields.Many2one(comodel_name='construction.deduction.addition', required=True,)
    account_id = fields.Many2one(comodel_name='account.account', required=True,)
    percentage = fields.Boolean(string='%')
    percentage_amount = fields.Float(string='% Amount')
    last_value = fields.Float('Last Value')
    value = fields.Float('current Value', compute="compute_current")
    total = fields.Float('Total Value', compute="compute_total")
    total_value = fields.Float('Total', compute="compute_total")
    contract_total_value = fields.Float('Total', compute="compute_contract_total")
    down_payment = fields.Boolean(string='Down Payment')

    @api.depends('total', 'percentage_amount','percentage', 'last_value')
    def compute_current(self):
        for rec in self:
            rec.value = (rec.move_id.current_value * rec.percentage_amount / 100) if rec.percentage is True else rec.total_value - rec.last_value

    @api.depends('percentage', 'percentage_amount','move_id.current_value')
    def compute_contract_total(self):
        for rec in self:
            rec.contract_total_value = rec.percentage_amount if rec.percentage is False else \
                rec.contract_id.total * rec.percentage_amount / 100

    @api.onchange('percentage', 'percentage_amount')
    def change_percentage(self):
        for rec in self:
            rec.value = rec.total_value - rec.last_value

    @api.onchange('name')
    def onchange_name(self):
        self.account_id = self.name.account_id.id
        self.percentage = self.name.percentage
        current = 0
        for line in self.move_id.invoice_line_ids:
            current += line.current_value

        self.percentage_amount = self.name.value
        # self.value = self.percentage_amount if self.percentage is False else (current * self.percentage_amount / 100)

        if self.move_id:
            res = {}
            lines = []

            deduction_lines = self.env['construction.deduction.addition'].search([
                ('to', '=', self.move_id.contract_id.type),
                ('type', '=', 'deduction'),
            ])
            # for line in self.move_id.contract_id.deduction_line_ids:
            for line in deduction_lines:
                # lines.append(line.name.id)
                lines.append(line.id)
            res['domain'] = {'name': [('id', 'in', lines)]}
            return res

    @api.depends('last_value', 'percentage', 'percentage_amount','move_id.invoice_total')
    def compute_total(self):
        for rec in self:
            rec.total = 0
            total = 0
            if rec.percentage is True:
                for line in rec.move_id.invoice_line_ids:
                    total += line.total_value
                rec.total_value = (rec.move_id.invoice_total * rec.percentage_amount / 100)
            else:
                rec.total_value = rec.percentage_amount
