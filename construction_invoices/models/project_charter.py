from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _name = 'project.charter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    project_id = fields.Many2one('construction.project2', required=True)
    date = fields.Date('Date')
    description = fields.Char('Description')
    benefit_expected = fields.Text('BENEFIT AND EXPECTED EFFECT (Key Deliverables):')
    assumptions = fields.Text('ASSUMPTIONS, RISKS AND RISK MITIGATION PLAN:')

    change_sponsor_id = fields.Many2one("res.users", string='Change Sponsor:')
    project_leader_id = fields.Many2one("res.users", string='Project Leader:')
    facilitator_id = fields.Many2one("res.users", string='Change Facilitator:')
    team_ids = fields.Many2many(comodel_name='res.users')

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    project_created = fields.Char('IS Project Plan Created ?')
    operating_budget = fields.Char('Operating Budget')
    external_cost = fields.Char('External costs')
    internal_expenses = fields.Char('Internal expenses')
    materials = fields.Char('Materials ')

