# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, fields, api, _

class Product(models.Model):
    _inherit = 'product.template'

    length = fields.Char(
        string='Length',
    )
    width = fields.Char(
        string='Width',
    )
    height = fields.Char(
        string='Height',
    )
    dimensions_uom_id = fields.Many2one(
        'uom.uom',
        'Dimension(UOM)',
        domain = lambda self:[('category_id','=',self.env.ref('uom.uom_categ_length').id)],
        help="Default Unit of Measure used for dimension."
    )

    weight_uom_id = fields.Many2one(
        'uom.uom',
        'Weight(UOM)',
        domain = lambda self:[('category_id','=',self.env.ref('uom.product_uom_categ_kgm').id)],
        help="Default Unit of Measure used for weight."
    )