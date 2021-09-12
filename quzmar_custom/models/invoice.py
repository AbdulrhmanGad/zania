from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    quzmar_type = fields.Selection(related="product_id.quzmar_type")
    new_quantity = fields.Float('Quantity')
    new_price = fields.Float('Unit Price')
    quzmar_length = fields.Float(string='Length', )
    quzmar_width = fields.Float(string='Width', )
    quzmar_height = fields.Float(string='Height', )
    size = fields.Float('Size', compute='compute_size')
    total_size = fields.Float('total Size (m2)', compute='compute_size')

    @api.onchange('new_price', 'total_size')
    def _onchange_new_price(self):
        self.price_unit = self.new_price * self.total_size

    @api.onchange('new_quantity')
    def _onchange_new_quantity(self):
        self.quantity = 1

    @api.depends('quzmar_length', 'quzmar_width', 'quzmar_height', 'new_quantity', 'quzmar_type')
    def compute_size(self):
        for rec in self:
            if rec.quzmar_type == 'length':
                rec.size = rec.quzmar_length / 100
            if rec.quzmar_type == 'width_height':
                rec.size = rec.quzmar_height * rec.quzmar_width / 10000
            if rec.quzmar_type == 'width_height_length':
                rec.size = rec.quzmar_length * rec.quzmar_height * rec.quzmar_width / 1000000
            rec.total_size = rec.size * rec.new_quantity

    @api.onchange('product_id')
    def quzmar_change_product2(self):
        if self.product_id.quzmar_type == 'width_height_length':
            self.quzmar_length = self.product_id.length
            self.quzmar_width = self.product_id.width
            self.quzmar_height = self.product_id.height
        if self.product_id.quzmar_type == 'width_height':
            self.quzmar_length = 0
            self.quzmar_width = self.product_id.width
            self.quzmar_height = self.product_id.height
        if self.product_id.quzmar_type == 'length':
            self.quzmar_length = self.product_id.length
            self.quzmar_width = 0
            self.quzmar_height = 0
            self.size = self.quzmar_height
        if self.product_id.quzmar_type is False:
            self.quzmar_length = self.quzmar_width = self.quzmar_height = False
            self.size = 0
            total_size = 0
