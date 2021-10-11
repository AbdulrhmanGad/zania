from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.move.line'
    project_id = fields.Many2one('construction.project2')


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    invoice_id = fields.Many2one('construction.invoice')
    subcontractor_id = fields.Many2one('res.partner', string="Subcontractor", )

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        self.partner_id = self.invoice_id.partner_id.id
        self.subcontractor_id = self.invoice_id.subcontractor_id.id


class ConstructionInvoice(models.Model):
    _name = 'construction.invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    construction_type = fields.Selection(string='Type',
                                         selection=[('owner', 'Owner'), ('subcontractor', 'Subcontractor')], )
    type = fields.Selection(string='Type', selection=[
        ('1', 'Processing'),
        ('2', 'Final')
    ])
    invoice_number = fields.Char('Invoice Number')
    date = fields.Date('Date', default=fields.Date.context_today,)
    due_date = fields.Date('Due Date')
    ref = fields.Char("Reference")
    contract_id = fields.Many2one(comodel_name='contract', string="Contract", required=True)
    move_id = fields.Many2one(comodel_name='account.move', string="Move")
    next_id = fields.Many2one(comodel_name='construction.invoice', string="Next")
    parent_id = fields.Many2one(comodel_name='construction.invoice', string="Parent")
    construction_project_id = fields.Many2one(related="contract_id.construction_project_id", string="Project")
    partner_id = fields.Many2one(related="contract_id.partner_id", string="Customer")
    subcontractor_id = fields.Many2one('res.partner', related="contract_id.subcontractor_id", string="Subcontractor")
    addition_line_ids = fields.One2many(comodel_name='addition.line', inverse_name='move_id')
    deduction_line_ids = fields.One2many(comodel_name='deduction.line', inverse_name='move_id')
    invoice_line_ids = fields.One2many(comodel_name='construction.invoice.line', inverse_name='invoice_id')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('journal', 'journal'),
        ('cancel', 'cancel'),
    ], default='draft')
    payment_ids = fields.One2many(comodel_name='account.payment', inverse_name='invoice_id', copy=False)
    payment_count = fields.Integer('Count', compute="compute_payment_count")
    total_value = fields.Float(string='total')
    last_value = fields.Float(string='Last Value', store=1)
    current_value = fields.Float(string='Current Value', compute='compute_due_amount', store=1)
    due_amount = fields.Float(string='Due Amount', compute='compute_due_amount', store=1)
    invoice_total = fields.Float(string='Invoice Total', compute='compute_due_amount', store=1)
    amount_paid = fields.Float(string='Amount Paid', compute='compute_paid', store=1)
    amount_difference = fields.Float(string='Amount Difference', compute='compute_paid', store=1)
    attachment = fields.Binary("Attachment")
    total_current_value = fields.Float(compute="compute_total_current", string="Current Value", store=True)
    total_current_ded = fields.Float(compute="compute_total_current", string="Current Deduction", store=True)
    total_current_add = fields.Float(compute="compute_total_current", string="Current Addition", store=True)
    amount_total = fields.Float(compute="compute_total_current", string="Amount Total", store=True)

    @api.depends('invoice_line_ids', 'deduction_line_ids')
    def compute_total_current(self):
        for rec in self:
            price = qty = ded = add = 0.0
            for line in rec.invoice_line_ids:
                price += line.price_unit
                qty += line.quantity
            rec.total_current_value = price * qty
            for ded in rec.deduction_line_ids:
                ded += ded.value
            rec.total_current_ded = ded
            for add in rec.addition_line_ids:
                add += add.value
            rec.total_current_add = add
            rec.amount_total = rec.total_current_value + rec.total_current_ded + rec.total_current_add

    @api.onchange('current_value')
    def _onchange_current_value(self):
        for line in self.addition_line_ids:
            line.change_percentage()
        for line in self.deduction_line_ids:
            line.change_percentage()

    @api.depends('invoice_line_ids', 'deduction_line_ids', 'addition_line_ids')
    def compute_due_amount(self):
        for rec in self:
            inv_tot = rec.due_amount = last_val = 0
            total_value = 0
            for line in rec.invoice_line_ids:
                # print(line.total_qty, "    ", line.price_unit, "   ", line.percentage)
                total_value += line.total_qty * line.price_unit * line.percentage / 100
                print("inv_tot ",inv_tot)
                inv_tot += line.total_value
                last_val += line.last_value
            rec.total_value = total_value
            rec.invoice_total = inv_tot
            rec.last_value = last_val
            rec.current_value = total_value - last_val
            total = total_value - last_val
            for add in rec.addition_line_ids:
                total += add.value

            for ded in rec.deduction_line_ids:
                total -= ded.value

            rec.due_amount = total

    # @api.depends('invoice_line_ids', 'deduction_line_ids', 'addition_line_ids')
    # def compute_due_amount(self):
    #     for rec in self:
    #         rec.due_amount, last_val = 0, 0
    #         total_value = 0
    #         for line in rec.invoice_line_ids:
    #             # print(line.total_qty, "    ", line.price_unit, "   ", line.percentage)
    #             total_value += line.total_qty * line.price_unit * line.percentage / 100
    #             last_val += line.last_value
    #         rec.total_value = total_value
    #
    #         # last_invoice_id = rec.env['construction.invoice'].search([
    #         #     ('id', '!=', rec.id),
    #         #     ('contract_id', '=', rec.contract_id.id),
    #         #     ('construction_type', '=', rec.construction_type),
    #         #     ('state', '=', 'journal'),
    #         # ], order='id desc', limit=1)
    #         rec.last_value = last_val
    #         rec.current_value = total_value - last_val
    #         total = total_value - last_val
    #         for add in rec.addition_line_ids:
    #             total += add.value
    #
    #         for ded in rec.deduction_line_ids:
    #             total -= ded.value
    #
    #         rec.due_amount = total

    @api.depends('amount_paid', 'amount_difference')
    def compute_payment_state(self):
        for rec in self:
            print(rec.amount_paid, ">>>>>>>>>>>>> ", rec.amount_difference)
            if rec.amount_paid == 0:
                rec.payment_state = 'not_paid'
            elif rec.amount_paid > 0 and rec.amount_paid < rec.due_amount:
                rec.payment_state = 'partial'
            elif rec.amount_paid > 0 and rec.amount_difference <= 0:
                rec.payment_state = 'paid'

    payment_state = fields.Selection(
        string='Payment State', selection=[
            ('not_paid', 'Not Paid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ], compute="compute_payment_state")

    @api.depends('payment_ids', 'due_amount')
    def compute_paid(self):
        for rec in self:
            total = 0
            for line in rec.payment_ids:
                if line.state == 'posted':
                    total += line.amount
            rec.amount_paid = total
            rec.amount_difference = rec.due_amount - total

    # @api.depends('current_value', 'deduction_line_ids', 'addition_line_ids')
    # def compute_due_amount(self):
    #     for rec in self:
    #         rec.due_amount = 0
    #         if 'New' not in str(rec.id):
    #             total_value = 0
    #             for line in rec.invoice_line_ids:
    #                 # print(line.total_qty, "    ", line.price_unit, "   ", line.percentage)
    #                 total_value += line.total_qty * line.price_unit * line.percentage / 100
    #             rec.total_value = total_value
    #
    #             last_invoice_id = rec.env['construction.invoice'].search([
    #                 ('id', '!=', rec.id),
    #                 ('contract_id', '=', rec.contract_id.id),
    #                 ('construction_type', '=', rec.construction_type),
    #                 ('state', '=', 'journal'),
    #             ], order='id desc', limit=1)
    #             rec.last_value = last_invoice_id.total_value
    #             rec.current_value = total_value - rec.last_value
    #             total = total_value - rec.last_value
    #             print("total ", total)
    #             for add in rec.addition_line_ids:
    #                 total += add.value
    #             print("total ", total)
    #
    #             for ded in rec.deduction_line_ids:
    #                 total -= ded.value
    #             print("total ", total)
    #
    #             rec.due_amount = total

    @api.onchange('invoice_line_ids')
    def change_total(self):
        for rec in self:
            rec.last_value = rec.current_value = total_value = 0
            for line in rec.invoice_line_ids:
                # print(line.total_qty, "    ", line.price_unit, "   ", line.percentage)
                total_value += line.total_qty * line.price_unit * line.percentage / 100
            rec.total_value = total_value
            if 'New' not in str(rec.id):
                last_invoice_id = rec.env['construction.invoice'].search([
                    ('id', '!=', rec.id),
                    ('contract_id', '=', rec.contract_id.id),
                    ('construction_type', '=', rec.construction_type),
                    ('state', '=', 'journal'),
                ], order='id desc', limit=1)
                # print(rec)
                # print(last_invoice_id, ">>>>>>>>>>>>>>>>> last", last_invoice_id.total_value)
                rec.last_value = last_invoice_id.total_value
                rec.current_value = total_value - rec.last_value

    @api.depends('payment_ids')
    def compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids.ids)

    def action_view_payment(self):
        self.ensure_one()
        action = self.env.ref("account.action_account_payments_payable").read()[0]
        action["domain"] = [("id", "in", self.payment_ids.ids)]
        if self.construction_type == 'owner':
            action['context'] = {
                'default_invoice_id': self.id,
                'default_payment_type': 'inbound',
                'default_amount': self.amount_difference
            }
        elif self.construction_type == 'subcontractor':
            action['context'] = {
                'default_invoice_id': self.id,
                'default_payment_type': 'outbound',
                'default_amount': self.amount_difference
            }
        return action

    @api.model
    def create(self, vals):
        if 'construction_type' in vals:
            print(vals)
            print(vals['construction_type'])
            if vals['construction_type'] == 'subcontractor':
                vals['name'] = self.env['ir.sequence'].next_by_code('sub.invoice')
            elif vals['construction_type'] == 'owner':
                vals['name'] = self.env['ir.sequence'].next_by_code('owner.invoice')
        return super(ConstructionInvoice, self).create(vals)

    def action_post(self):
        self.state = 'confirm'

    def cancel(self):
        if self.move_id:
            raise ValidationError(_('You Can not cancel invoice that has journal'))
        self.state = 'cancel'

    def reset_draft(self):
        if self.move_id:
            raise ValidationError(_('You Can not Draft invoice that has journal'))
        self.state = 'draft'

    def create_journal(self):
        if not self.invoice_line_ids:
            raise ValidationError(_('There is not invoice lines !!'))
        if self.construction_type == 'owner':
            journal_id = self.env['ir.config_parameter'].sudo().get_param('base_setup.journal_id')
            if not journal_id:
                raise ValidationError(_('please add Owner Journal in company profile'))
        if self.construction_type == 'subcontractor':
            sub_journal_id = self.env['ir.config_parameter'].sudo().get_param('base_setup.sub_journal_id')
            if not sub_journal_id:
                raise ValidationError(_('please add Subcontractor Journal in company profile'))
        move_id = self.env['account.move'].create({
            'journal_id': int(self.env['ir.config_parameter'].sudo().get_param('base_setup.journal_id')) if self.construction_type == 'owner' else int(self.env['ir.config_parameter'].sudo().get_param('base_setup.sub_journal_id')),
            "partner_id": self.partner_id.id,
            'move_type': 'entry',
            'ref': self.name
        })
        if self.construction_type == 'owner':
            add_total = deduction_total = 0
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                "project_id": self.contract_id.construction_project_id.id,
                "account_id": self.contract_id.account1_id.id,
                "name": 'Invoice Value',
                "debit": 0,
                "credit": self.current_value,
                "partner_id": self.partner_id.id,
            })
            for line in self.addition_line_ids:
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    "move_id": move_id.id,
                    "project_id": self.contract_id.construction_project_id.id,
                    "account_id": line.account_id.id,
                    "name": line.name.name,
                    "debit": 0,
                    "credit": line.value,
                    "partner_id": self.partner_id.id,
                })
                add_total += line.value
            for line in self.deduction_line_ids:
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    "move_id": move_id.id,
                    "project_id": self.contract_id.construction_project_id.id,
                    "account_id": line.account_id.id,
                    "name": line.name.name,
                    "credit": 0,
                    "debit": line.value,
                    "partner_id": self.partner_id.id,
                })
                deduction_total += line.value

            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                "project_id": self.contract_id.construction_project_id.id,
                "account_id": self.contract_id.account2_id.id,
                "name": 'Due Amount',
                "credit": 0,
                "debit": self.current_value + add_total - deduction_total,
                "partner_id": self.partner_id.id,
            })
        elif self.construction_type == 'subcontractor':
            add_total = deduction_total = 0
            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                "project_id": self.contract_id.construction_project_id.id,
                "account_id": self.contract_id.account1_id.id,
                "name": 'Invoice Value',
                "credit": 0,
                "debit": self.current_value,
                "partner_id": self.subcontractor_id.id,
            })
            for line in self.addition_line_ids:
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    "move_id": move_id.id,
                    "project_id": self.contract_id.construction_project_id.id,
                    "account_id": line.account_id.id,
                    "name": line.name.name,
                    "credit": 0,
                    "debit": line.value,
                    "partner_id": self.subcontractor_id.id,
                })
                add_total += line.value
            for line in self.deduction_line_ids:
                self.env['account.move.line'].with_context(check_move_validity=False).create({
                    "move_id": move_id.id,
                    "project_id": self.contract_id.construction_project_id.id,
                    "account_id": line.account_id.id,
                    "name": line.name.name,
                    "debit": 0,
                    "credit": line.value,
                    "partner_id": self.subcontractor_id.id,
                })
                deduction_total += line.value

            self.env['account.move.line'].with_context(check_move_validity=False).create({
                "move_id": move_id.id,
                "project_id": self.contract_id.construction_project_id.id,
                "account_id": self.contract_id.account2_id.id,
                "name": "Due Amount",
                "debit": 0,
                "credit": self.current_value + add_total - deduction_total,
                "partner_id": self.subcontractor_id.id,
            })
        self.move_id = move_id.id
        self.state = 'journal'

    @api.constrains('contract_id')
    def constrains_contract_id(self):
        last_invoice_id = self.env['construction.invoice'].search([
            ('id', '!=', self.id),
            ('contract_id', '=', self.contract_id.id),
            ('construction_project_id', '=', self.contract_id.construction_project_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('construction_type', '=', self.construction_type),
            ('state', '=', 'journal'),
        ], order='id desc', limit=1)
        # if not the first time
        if last_invoice_id:
            print(last_invoice_id.invoice_line_ids)
            total_value = 0
            for inv_line in last_invoice_id.invoice_line_ids:
                print(inv_line, ">pro<", inv_line.product_id)
                if inv_line.product_id:
                    ln = self.env['construction.invoice.line'].create({
                        'invoice_id': self.id,
                        # 'account_id': inv_line.account_id.id,
                        'product_id': inv_line.product_id.id,
                        'contract_qty': inv_line.contract_qty,
                        'last_qty': inv_line.total_qty,
                        'quantity': 0,
                        'percentage': inv_line.percentage,
                        'total_qty': inv_line.total_qty,
                        'price_unit': inv_line.price_unit,
                        'last_value': inv_line.total_value,
                    })
                    total_value += inv_line.total_qty * inv_line.price_unit * inv_line.percentage
            self.last_value = last_invoice_id.total_value
            for add in last_invoice_id.addition_line_ids:
                self.env['addition.line'].create({
                    'move_id': self.id,
                    'name': add.name.id,
                    'account_id': add.account_id.id,
                    'percentage': add.percentage,
                    'percentage_amount': add.percentage_amount,
                    'last_value': add.total_value,
                    'value': 0,
                    'total_value': 0,
                })
            for ded in last_invoice_id.deduction_line_ids:
                self.env['deduction.line'].create({
                    'move_id': self.id,
                    'name': ded.name.id,
                    'account_id': ded.account_id.id,
                    'percentage': ded.percentage,
                    'percentage_amount': ded.percentage_amount,
                    'last_value': ded.total_value,
                    'value': 0,
                    'total_value': 0,
                })
            last_invoice_id.next_id = self.id
            self.parent_id = last_invoice_id.id
        else:
            # for invoice_line in self.invoice_line_ids:
            #     invoice_line.unlink()
            # for line in self.contract_id.line_ids:
            #     ln = self.env['construction.invoice.line'].create({
            #         'invoice_id': self.id,
            #         # 'account_id': line.product_id.property_account_income_id.id if line.product_id.property_account_income_id else
            #         # line.product_id.categ_id.property_account_income_categ_id.id,
            #         'product_id': line.product_id.id,
            #         'last_qty': 0,
            #         'quantity': line.quantity,
            #         'total_qty': line.quantity,
            #         'price_unit': line.price_unit,
            #     })
            for a in self.addition_line_ids:
                a.unlink()
            for add in self.contract_id.addition_line_ids:
                self.env['addition.line'].create({
                    'move_id': self.id,
                    'name': add.name.id,
                    'account_id': add.account_id.id,
                    'percentage': add.percentage,
                    'percentage_amount': add.percentage_amount,
                    'last_value': 0,
                    'value': add.value,
                    'total_value': add.percentage_amount
                    # if add.percentage is False else  add.contract_id.total * add.percentage_amount / 100,
                })

            for d in self.deduction_line_ids:
                d.unlink()
            for ded in self.contract_id.deduction_line_ids:
                self.env['deduction.line'].create({
                    'move_id': self.id,
                    'account_id': ded.account_id.id,
                    'name': ded.name.id,
                    'percentage': ded.percentage,
                    'percentage_amount': ded.percentage_amount,
                    'last_value': 0,
                    'value': ded.contract_total_value,
                    'total_value': ded.percentage_amount
                    # if add.percentage is False else add.contract_id.total * add.percentage_amount / 100,
                })

        for ded in self.deduction_line_ids:
            ded.compute_current()
        for add in self.addition_line_ids:
            add.compute_current()

    # def unlink(self):
    #     for rec in self:
    #         if rec.next_id:
    #             raise ValidationError(_("You Can not Delete invoice which generate other one based on it"))
    #     return super(ConstructionInvoice, self).unlink()


class ConstructionInvoiceLine(models.Model):
    _name = 'construction.invoice.line'

    invoice_id = fields.Many2one('construction.invoice')

    construction_type = fields.Selection(string='Type', related='invoice_id.construction_type')
    name = fields.Char('Description')
    product_id = fields.Many2one('tender.line', required=1)
    price_unit = fields.Float(string='Price Unit', conpute="compute_contract_qty_price", store=1)
    percentage = fields.Float(string='Percentage', default=100)
    contract_qty = fields.Float(string='Contract Qty', conpute="compute_contract_qty_price", store=1)
    quantity = fields.Float(string='Current Qty')
    last_qty = fields.Float(string='Last Qty')
    price_subtotal = fields.Float(string='Price Subtotal', compute='compute_price_subtotal', store=1)
    total_qty = fields.Float(string='Total Quantity', compute='compute_qty', store=1)
    remaining_qty = fields.Float(string='Remaining Qty', compute='compute_remaining_qty', store=1)
    total_subtotal = fields.Float(string='Total ', compute='compute_total_subtotal', store=1)
    total_value = fields.Float(string='total', compute='computes_total', store=1)
    last_value = fields.Float(string='Last Value', store=True)
    current_value = fields.Float(string='Current Value', compute='computes_total', store=1)
    wbs_line_id = fields.Many2one(comodel_name='wbs.line', string="Wbs Item", )
    competition_per = fields.Float(  string='Competition Percentage', compute="compute_competition_per", store=1)

    @api.depends('total_qty', 'contract_qty')
    def compute_remaining_qty(self):
        for rec in self:
            rec.remaining_qty = rec.contract_qty -  rec.total_qty

    @api.depends('total_qty', 'contract_qty')
    def compute_competition_per(self):
        for rec in self:
            rec.competition_per = rec.total_qty / rec.contract_qty if rec.contract_qty > 0 else 0

    @api.onchange('wbs_line_id', 'product_id')
    def change_wbs_line_id(self):
        if not self.invoice_id.contract_id:
            raise ValidationError(_("Please Select Contract "))
        if self.invoice_id.contract_id:
            res = {}
            lines = []
            for contract_line in self.invoice_id.contract_id.line_ids:
                if self.product_id == contract_line.product_id:
                    if contract_line.wbs_line_id.type == 'child':
                        lines.append(contract_line.wbs_line_id.id)
            if len(lines)>0:
                res['domain'] = {'wbs_line_id': [('id', 'in', lines)]}
            else:
                res['domain'] = {'wbs_line_id': [('id', 'in', False)]}
            return res

    @api.depends('last_value', 'percentage', 'total_qty')
    def computes_total(self):
        for rec in self:
            print(rec.total_qty, " XXX ", rec.price_unit, "  >>>> ", rec.percentage)
            rec.total_value = rec.total_qty * rec.price_unit * rec.percentage / 100
            rec.current_value = rec.total_value - rec.last_value


    @api.onchange('product_id')
    def change_product_id_domain(self):
        res = {}
        products = []
        for line in self.invoice_id.contract_id.line_ids:
            products.append(line.product_id.id)
        res['domain'] = {'product_id': [('id', 'in', products)]}
        return res

    @api.depends('product_id')
    def compute_contract_qty_price(self):
        for rec in self:
            rec.contract_qty = 0
            rec.price_unit = 0
            for line in rec.invoice_id.contract_id.line_ids:
                if rec.product_id == line.product_id:
                    rec.contract_qty = line.quantity
                    rec.price_unit = line.price_unit

    @api.onchange('product_id')
    def change_product_id(self):
        for line in self.invoice_id.contract_id.line_ids:
            if self.product_id == line.product_id:
                self.contract_qty = line.quantity
                self.price_unit = line.price_unit
                # for line in self.invoice_id.invoice_line_ids:
        #     if self.product_id == line.product_id and line != self:
        #         raise ValidationError(_("Item [ %s ] Already Exist " % self.product_id.name))

    @api.depends('quantity')
    def compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = 0

    @api.depends('last_qty', 'quantity')
    def compute_qty(self):
        for rec in self:
            rec.total_qty = rec.last_qty + rec.quantity

    @api.onchange('quantity')
    def _onchange_quantity_valid(self):
        print(self.last_qty + self.quantity, "***************** ", self.contract_qty)
        if (self.last_qty + self.quantity) > self.contract_qty:
            raise ValidationError(_("Total Quantity Must be les than or equal contract Quantity"))

    @api.depends('total_qty', 'price_unit')
    def compute_total_subtotal(self):
        for rec in self:
            rec.total_subtotal = rec.total_qty * rec.price_unit
