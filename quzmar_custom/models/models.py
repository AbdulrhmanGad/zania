# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('1', 'Length'),
        ('2', 'Width * Height'),
        ('3', 'Width * Height * Length')], required=True, )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('1', 'Length'),
        ('2', 'Width * Height'),
        ('3', 'Width * Height * Length')], required=True, )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    quzmar_type = fields.Selection(string='Type', related='product_id.quzmar_type')
    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    size = fields.Float('Size', compute='compute_size')
    total_size = fields.Float('total Size (m2)')

    @api.depends('length', 'width', 'height', 'product_uom_qty')
    def compute_size(self):
        for rec in self:
            if rec.quzmar_type == '1':
                rec.size = rec.length / 100
            if rec.quzmar_type == '2':
                rec.size = rec.height * rec.width / 10000
            if rec.quzmar_type == '3':
                rec.size = rec.length * rec.height * rec.width /1000000
            rec.total_size = rec.size * rec.product_uom_qty

    @api.onchange('product_id')
    def quzmar_change_product(self):
        self.length = self.product_id.length if self.product_id.quzmar_type in ['1', '3'] else 0
        self.width = self.product_id.width if self.product_id.quzmar_type in ['2', '3'] else 0
        self.height = self.product_id.height if self.product_id.quzmar_type in ['2', '3'] else 0

    @api.onchange('FIELD_NAME')
    def calc_price(self):
        pass