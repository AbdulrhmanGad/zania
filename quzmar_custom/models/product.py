# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('No', 'Nothing'),
        ('length', 'Length'),
        ('width_height', 'Width * Height'),
        ('width_height_length', 'Width * Height * Length')], required=True, )

    @api.model
    def create(self, values):
        res = super(ProductTemplate, self).create(values)
        print("RRRRRRRRRRRRRRRRRRRRRRRRRR", res)
        print("RRRRRRRRRRRRRRRRRRRRRRRRRR", res.product_variant_ids)
        for product in res.product_variant_ids:
            product.write({
                'length': product.length,
                'width': product.width,
                'height': product.height,
                'quzmar_type': product.quzmar_type,
            })
        return res

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        print("Create ?>>>>>>>>>>>>>> ", res)
        print("Create ?>>>>>>>>>>>>>> ", res.product_variant_ids)
        for product in res.product_variant_ids:
            product.write({
                'length': res.length,
                'width': res.width,
                'height': res.height,
                'quzmar_type': res.quzmar_type,
            })
        return res

    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        print("XXXXXXXXwrite", values)
        if 'length' in values:
            for product in self.product_variant_ids:
                product.write({'length': values['length']})
        if 'width' in values:
            for product in self.product_variant_ids:
                product.write({'width': values['width']})
        if 'height' in values:
            for product in self.product_variant_ids:
                product.write({'height': values['height']})
        if 'quzmar_type' in values:
            for product in self.product_variant_ids:
                product.write({'quzmar_type': values['quzmar_type']})
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    length = fields.Float(string='Length', )
    width = fields.Float(string='Width', )
    height = fields.Float(string='Height', )
    quzmar_type = fields.Selection(string='Type', selection=[
        ('No', 'Nothing'),
        ('length', 'Length'),
        ('width_height', 'Width * Height'),
        ('width_height_length', 'Width * Height * Length')], required=True, )
