# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('length', 'Length'),
        ('width_height', 'Width * Height'),
        ('width_height_length', 'Width * Height * Length')], required=True, )

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        if 'length' in values:
            for product in self.product_variant_ids:
                product.write({'length': values['length']})
        if 'width' in values:
            for product in self.product_variant_ids:
                product.write({'width': values['width']})
        if 'height' in values:
            for product in self.product_variant_ids:
                product.write({'height':values['height']})
        if 'quzmar_type' in values:
            for product in self.product_variant_ids:
                product.write({'quzmar_type':values['quzmar_type']})
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('length', 'Length'),
        ('width_height', 'Width * Height'),
        ('width_height_length', 'Width * Height * Length')], required=True, )
