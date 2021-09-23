from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'
    journal_id = fields.Many2one('account.journal', string="Owner Journal")
    sub_journal_id = fields.Many2one('account.journal', string="Subcontractor Journal")


class ConstructionItem(models.Model):
    _name = 'construction.item'

    name = fields.Char('Name', required=True)
    uom_id = fields.Many2one('uom.uom', required=True)


class ConstructionProject(models.Model):
    _name = 'construction.project2'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    description = fields.Html('Description')
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    manager_id = fields.Many2one('res.partner', string="Manager", )
    consultant_id = fields.Many2one('res.partner', string="Consultant", )
    type_id = fields.Many2one('construction.project2.type', string="Type", required=False)
    date = fields.Date('Date', default=fields.Date.today)
    create_date = fields.Date('Create Date', default=fields.Date.today, readonly=1)
    attachment = fields.Binary("Attachment")
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    tender_line_ids = fields.One2many(comodel_name='tender.line', inverse_name='construction_id')
    breakdown_ids = fields.One2many(comodel_name='break.down', inverse_name='project_id', )
    breakdown_count = fields.Integer(compute='compute_breakdown_count')

    def create_financial_offer(self):
        x = self.breakdown_ids.filtered(lambda l: l.state == 'financial')
        if len(x.ids) >= 1:
            offer_id = self.env['financial.offer'].create({
                'partner_id': self.partner_id.id,
                'project_id': self.id,
                'date': fields.Datetime.today()
            })
            for line in self.tender_line_ids:
                self.env['financial.offer.line'].create({
                    'offer_id': offer_id.id,
                    'name': line.name,
                    'item_id': line.item_id.id,
                    'break_down_id': line.break_down_id.id,
                    'tender_id': line.id,
                    'description': line.description ,
                    'type': line.type,
                    'qty': line.qty,
                    'uom_id': line.uom_id.id,
                    'price': line.price,
                    'total': line.total,
                    'note': line.note,
                })

        else:
            raise ValidationError(_('At least One break Down must in State financial'))

    @api.depends('breakdown_ids')
    def compute_breakdown_count(self):
        for rec in self:
            rec.breakdown_count = len(rec.breakdown_ids.ids)

    def create_breakdown(self):
        for line in self.tender_line_ids:
            if line.type != 'view' and not line.break_down_id:
                break_down_id = self.env['break.down'].create({
                    'project_id': line.construction_id.id,
                    'analytic_account_id': self.analytic_account_id.id,
                    'tender_line_id': line.id,
                    'code': line.name,
                    'description': line.description,
                    'name': line.name,
                    'item_id': line.item_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.qty,
                    'type': line.type,
                    # 'sale_price': 0,
                    'note': line.note,
                })
                line.break_down_id = break_down_id.id

    def action_view_breakdown(self):
        action = self.env.ref("construction_invoices.breakdown_action")
        result = action.read()[0]
        result["domain"] = [("id", "in", self.breakdown_ids.ids)]
        return result

    @api.model
    def create(self, vals):
        res = super(ConstructionProject, self).create(vals)
        analytic_account_id = self.env['account.analytic.account'].create({
            'name': res.name,
            'partner_id': res.partner_id.id,
        })
        res.analytic_account_id = analytic_account_id.id
        return res

    @api.constrains('tender_line_ids')
    def constrains_name(self):
        for rec in self:
            for line1 in rec.tender_line_ids:
                for line2 in rec.tender_line_ids:
                    if line1.id != line2.id and line1.name == line2.name:
                        raise ValidationError(_("Code [ %s ] Must be unique in one the project") % line2.name)


class TenderLine(models.Model):
    _name = 'tender.line'

    construction_id = fields.Many2one('construction.project2')
    name = fields.Char('code', required=1)
    item_id = fields.Many2one('construction.item', required=True)
    break_down_id = fields.Many2one('break.down')
    description = fields.Text('Description', required=True)
    uom_id = fields.Many2one('uom.uom')
    qty = fields.Float('Qty')
    price = fields.Float('Price', compute='compute_price')
    total = fields.Float(compute="compute_total")
    note = fields.Char()
    type = fields.Selection(string='Type', selection=[('view', 'View'), ('transaction', 'Transaction')]
                            , default='view', required=True)

    @api.depends('break_down_id')
    def compute_price(self):
        for rec in self:
            rec.price = rec.break_down_id.sale_price_amount

    @api.depends('price', 'qty')
    def compute_total(self):
        for rec in self:
            rec.total = rec.qty * rec.price

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        super(TenderLine, self).name_search(name)
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('description', operator, name)]
        results = self.search(domain + args, limit=limit)
        return results.name_get()

    @api.depends('description', 'description')
    def name_get(self):
        result = []
        for rec in self:
            name = ('[ %s ] %s' % (rec.name, rec.description))
            result.append((rec.id, name))
        return result


class ConstructionProjectType(models.Model):
    _name = 'construction.project2.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
