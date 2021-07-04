from odoo import fields, models,api
from odoo.models import Model

class menu(Model):
    _inherit = "ir.ui.menu"
    _order = "name asc"
