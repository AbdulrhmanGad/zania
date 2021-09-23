from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinancialOffer(models.Model):
    _name = 'financial.offer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner')
    project_id = fields.Many2one('construction.project2')
    date = fields.Date(string='Date', )
    discount_type = fields.Selection(string='Discount Type', default='line',
                                     selection=[('line', 'Line'), ('total', 'Total'), ])
    discount = fields.Float('Discount')
    date = fields.Date(string='Date', )
    line_ids = fields.One2many(comodel_name='financial.offer.line', inverse_name='offer_id')
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),
                   ('confirm', 'Confirm'), ],
        required=False, )
    total = fields.Float("Total", compute="compute_total")
    total_discount = fields.Float("Discount", compute="compute_total_discount")
    total_all = fields.Float("Total", compute="compute_total_all")

    def unlink(self):
        if self.state != 'draft':
            raise  ValidationError(_("Can not Delete Confirmed Financial Offer"))
        return super(FinancialOffer, self).unlink()

    @api.depends('line_ids')
    def compute_total_all(self):
        for rec in self:
            total = sum(line.total for line in rec.line_ids)
            discount_amount = sum(line.discount_amount for line in rec.line_ids)
            rec.total_all = total - discount_amount

    @api.depends('line_ids')
    def compute_total(self):
        for rec in self:
            rec.total = sum(line.total for line in rec.line_ids)

    @api.depends('line_ids', 'discount')
    def compute_total_discount(self):
        for rec in self:
            discount = 0
            for line in rec.line_ids:
                if line.discount:
                    discount += line.discount / 100 * line.price * line.qty
            rec.total_discount = discount

    @api.onchange('discount_type', 'discount', 'line_ids')
    def _onchange_discount_type(self):
        if self.discount_type == 'total':
            for line in self.line_ids:
                line.discount = self.discount
        else:
            self.discount = 0

    def action_confirm(self):
        self.state = 'confirm'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('financial.offer')
        return super(FinancialOffer, self).create(vals)


class FinancialOfferLine(models.Model):
    _name = 'financial.offer.line'

    offer_id = fields.Many2one('financial.offer')
    name = fields.Char('code', required=1)
    item_id = fields.Many2one('construction.item', required=True)
    break_down_id = fields.Many2one('break.down', )
    tender_id = fields.Many2one('tender.line', )
    description = fields.Text('Description', required=True)
    uom_id = fields.Many2one('uom.uom')
    qty = fields.Float('Qty')
    price = fields.Float('Price')
    discount = fields.Float('Disc %')
    discount_amount = fields.Float('Discount', compute="compute_discount")
    total_after_disc = fields.Float("Total", compute="compute_total")
    total = fields.Float(compute="compute_total")
    note = fields.Char()
    type = fields.Selection(string='Type', selection=[('view', 'View'), ('transaction', 'Transaction')]
                            , default='view', required=True)

    @api.depends('discount', 'qty', 'price')
    def compute_discount(self):
        for rec in self:
            rec.discount_amount = rec.discount / 100 * rec.qty * rec.price

    @api.depends('price', 'qty', 'discount')
    def compute_total(self):
        for rec in self:
            rec.total = rec.price * rec.qty
            if rec.discount:
                discount = rec.discount / 100 * rec.price * rec.qty
                rec.total_after_disc = (rec.price * rec.qty) - discount
            else:
                rec.total_after_disc = rec.price * rec.qty
