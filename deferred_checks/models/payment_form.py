# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning


class ResPartner(models.Model):
     _inherit = 'res.partner'
     max_check_amount= fields.Float('Maximum Checks Amount')


class MoveState(models.Model):

    _inherit = 'account.move.line'
    check_state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('transfer_to_vendor', 'Transferred To Vendor'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('drawcash','Draw Cash'),
                              ('issue', 'Issued Deferred')], string='State')
    check_id = fields.Many2one('checks.paid',string='check_id')
    is_checks_fees=fields.Boolean(string =" is have checks fees")

'''
class ResBank(models.Model):
    _inherit = "res.bank"

    company_id = fields.Many2one('res.company', string='Company')
    branch_name = fields.Char(string='Branch Name')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('filter_comapny_id'):
            bank_list = []
            bank_ids = self.env['res.bank'].search([('company_id', '=', self.env.user.company_id.id)])
            for each in bank_ids:
                bank_list.append(each.id)
            if bank_list:
                bank_id = self.env['res.bank'].browse(bank_list)
                return bank_id.name_get()
            else:
                bank_ids = self.env['res.bank'].search([]).ids
                return self.env['res.bank'].browse(bank_ids).name_get()

        else:
            bank_ids = self.env['res.bank'].search([]).ids
            return self.env['res.bank'].browse(bank_ids).name_get()
'''


# class account_abstract_payment(models.Model):
#     _name = "account.payment"
#     #Abdulrhamn _inherit = "account.abstract.payment"
#
#     payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type', required=True, track_visibility='always')
#     partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='always')
#     amount = fields.Monetary(string='Payment Amount', required=True, track_visibility='always')


class PaymentJournalExtends(models.Model):
    _inherit = ['account.journal']
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name:
            name = '%' + '%'.join(name.split()) + '%'
        return super(PaymentJournalExtends,self).name_search(name,args,operator,limit)


class PaymentFromExtends(models.Model):
    _name = 'account.payment'
#     _inherit = 'account.payment'
    _inherit = ['account.payment', 'mail.thread']
    is_edit=fields.Boolean(string ="is edit button", default=False)
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled')],
                                 readonly=True, default='draft', copy=False, string="Status", track_visibility='always')
    transferred_check = fields.Boolean(string='Transferred Check', default=False)
    checks_paid = fields.One2many('checks.paid', 'payment_form', string='Checks')
    #                                   track_visibility='always')

    transferred_checks = fields.Many2many('checks.paid', 'payment_form', string='Checks', track_visibility='always', domain=['|',('check_type','=','inbound'),('check_type','=','outbound')])
    check_number = fields.Char('check Number')
    due_date = fields.Date('Due Date', track_visibility='always')
    bank_account = fields.Many2one('res.bank', string='Bank')
    branch_no = fields.Char(string='Branch No')
    branch_name = fields.Char(string='Branch Name')
    customer_bank_acc = fields.Char(string='Customer Bank Account')
    avg_days = fields.Char('Average Days', track_visibility='always')
    ch_amount = fields.Float('ch amount')
    received_date= fields.Date('Received Date')
    sales_person = fields.Many2one('res.sales.person',string='Sales Person')
    admin_check_field = fields.Boolean('Check', compute='get_user_group')

    @api.depends('partner_id')
    def get_user_group(self):
        if (self.env.user.id == 10) or (self.env.user.id==1):
           self.admin_check_field = True
        else :
            self.admin_check_field = False

    @api.onchange('currency_id')
    def onchange_currency(self):
        if self.currency_id.id == self.env.user.company_id.currency_id.id:
            return {'domain' : {'journal_id':[('currency_id', 'in', [self.env.user.company_id.currency_id.id, False])],'transferred_checks':[('currency_id', 'in', [self.env.user.company_id.currency_id.id, False])]}}
        else:
            return {'domain' : {'transferred_checks':[('currency_id','=',self.currency_id.id)],'journal_id':[('currency_id','=',self.currency_id.id)]}}

    def validate_amount(self):
        #date = datetime.strptime(self.payment_date, '%d-%m-%Y')
        past_amount = 0
        if not self.partner_id:
            return 0
        #current_checks = [check.id for check in self.checks_paid if type(check) != models.NewId]
        '''
        self.env.cr.execute("select id from checks_paid where due_date > '%s' and issuer_names = %s"%(self.date,self.partner_id.id))
        checks_recieved = self.env.cr.dictfetchall()
        past_id = [check['id'] for check in checks_recieved if check['id'] not in current_checks]
        print past_id
        checks = self.env['checks.paid'].search([('id' ,'in',past_id)])
        '''
        #print current_checks
        checks = self.env['checks.paid'].search([('due_date','>',self.date),('issuer_names','=',self.partner_id.id),('id','not in',self.checks_paid.ids)])
        #self.env['checks.paid'].search([('due_date','>',date), ('state','=','received'), ('issuer_names','=',self.partner_id.id),('payment_form','!=',self.id),('payment_form','!=',False)])
        for check in checks:
            rate = check.payment_form.currency_rate or check.payment_form.currency_id.rate
            try:
                past_amount = past_amount + ( check.check_amount * rate )
            except:
                past_amount = past_amount + ( check.amount * rate )

        return past_amount

    def check_max_amount(self):
        if not self.partner_id.max_check_amount or self.partner_id.max_check_amount <= 0:
            return
        past_amount = self.validate_amount()
        amount = self.amount * (self.currency_rate or self.currency_id.rate)
        if self.amount and self.payment_type == 'inbound':
             if self.partner_id.max_check_amount:
                 if self.partner_id.max_check_amount < (amount+past_amount):
                    #print 'its true !'
                    #return {'warning': {'title': _('Checks Amount'), 'message': _('%s Maximum Checks Amount is %s and current not deposited checks %s!!!' %(self.partner_id.name,self.partner_id.max_check_amount, amount)),},}
                    return True
        return False

    
    def unlink(self):
        #unlink all ckecks
        for each in self.transferred_checks:
            each.is_selected_check=False

        for rec in self:
            if rec.state == 'confirmed':
                raise Warning(_('Can not delete posted payment'))
            for check in rec.checks_paid:
                check.unlink()
            #for check in rec.transferred_checks:
            #    check.unlink()
        return super(PaymentFromExtends, self).unlink()

        #deleted =

    def check_cust_max_amount(self):

        if not self.partner_id.max_check_amount or self.partner_id.max_check_amount <= 0:
            return
        amount = self.validate_amount()
        check = self.check_max_amount()
        msg = _('%s Maximum Checks Amount is %s ILS and current not deposited checks %s ILS and you try to add %s %s' %(self.partner_id.name,self.partner_id.max_check_amount, amount, self.amount,self.currency_id.symbol))
        if check:
            return {'warning': {'title': _('Checks Amount'), 'message': msg,},}

    @api.onchange('checks_paid')
    def checks_paid_number(self):
        list = []
        check_amount = []
        if self.checks_paid:
            each =  self.checks_paid[-1]
            self.check_number = str(int(each.name) + 1)
            self.due_date = datetime.strptime(each.due_date, '%Y-%m-%d')
            date = datetime.today()
            str_date = date.strftime('%Y-%m-%d')
            if (self.due_date < str_date):
                msg = _(' The Due Date of the checks is invalid ')

                return {'warning': {'title': _('Checks date'), 'message': msg,},}

            self.bank_account = each.bank_account
            self.branch_no = each.branch_no
            self.branch_name = each.branch_name
            self.customer_bank_acc = each.customer_bank_acc
            self.received_date = each.received_date
        for each in self.checks_paid:
            check_amount.append(each.amount)
            self.amount= sum(check_amount)

            if each.due_date:

                list.append(((datetime.strptime(each.due_date, '%Y-%m-%d') - datetime.strptime(self.date, '%Y-%m-%d')).days) * each.amount)
                self.avg_days = round(sum(list) / self.amount)
        self.ch_amount = sum(check_amount)

    def check_total_save(self):
        if not self.partner_id.max_check_amount or self.partner_id.max_check_amount <= 0:
            return
        amount = self.validate_amount()
        check = self.check_max_amount() #on save
        msg = _('%s Maximum Checks Amount is %s ILS and current not deposited checks %s ILS and you try to add %s %s' %(self.partner_id.name,self.partner_id.max_check_amount, amount, self.amount,self.currency_id.symbol))
        if(check):
            raise UserError(msg)

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(
            date=self.date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id,
                                                          invoice_currency)

        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.date).compute_amount_fields(
                self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            # the writeoff debit and credit must be computed from the invoice residual in company currency
            # minus the payment amount in company currency, and not from the payment difference in the payment currency
            # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            total_payment_company_signed = self.currency_id.with_context(date=self.date).compute(self.amount,
                                                                                                         self.company_id.currency_id)
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                amount_wo = total_payment_company_signed - total_residual_company_signed
            else:
                amount_wo = total_residual_company_signed - total_payment_company_signed
            debit_wo = amount_wo > 0 and amount_wo or 0.0
            credit_wo = amount_wo < 0 and -amount_wo or 0.0
            writeoff_line['name'] = _('Counterpart')
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo
        self.invoice_ids.register_payment(counterpart_aml)

        # Write counterpart lines
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        if self.transferred_check == True:
            for each in self.transferred_checks:
                vals = {
                    'name': self.name,
                    'account_id': self.env['account.account'].search([('code','=','111100')] ,limit=1).id,#each.issuer_names.property_account_receivable_id.id,
                    'payment_id': self.id,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
                    'credit': each.amount,
                    #'partner_id': each.issuer_name.id,
                    'partner_id': each.check_type in ('inbound', 'outbound') and
                          self.env['res.partner']._find_accounting_partner(each.issuer_names).id or False,
                }
                liquidity_aml_dict.update(vals)
                aml_obj.create(liquidity_aml_dict)
        else:
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        move.post()
        return move

    
    def isValidChecks(self):
        #check if payment is check type  and list is empty
        if (self.transferred_checks):
            count=0
            for each in self.transferred_checks:
                if each.is_selected_check:
                    raise UserError(_(" this check  %s is exist in another payment ") %each.name)


            for each in self.transferred_checks:
                each.is_selected_check=True
        if(self.transferred_check):
            if not self.transferred_checks or len(self.transferred_checks) == 0:

                return False
            ch_amount = sum([check.amount for check in self.transferred_checks])
            if not self.amount == ch_amount:
                self.amount = ch_amount
        elif(self.payment_method_id.code == 'check_printing'):
            if not self.checks_paid or len(self.checks_paid) == 0:

                return False
            ch_amount = sum([check.amount for check in self.checks_paid])
            if not self.amount == ch_amount:
                self.amount = ch_amount
            #make sure that amount setted to be right

        return True

    
    def write(self, vals):
        old_trans=self.transferred_checks
        res = super(PaymentFromExtends, self).write(vals)
        for each in old_trans:
            if each not in self.transferred_checks:
                each.is_selected_check=False
        for each in self.transferred_checks:
            each.is_selected_check=False

        #self.validate_amount()
        is_valid = self.isValidChecks()

        if not is_valid:
            raise UserError(_("Please fill check list! Or flag this as cash payment"))
        return res

    @api.model
    def create(self, vals):
        res = super(PaymentFromExtends, self).create(vals)
        is_valid = res.isValidChecks()
        if not is_valid:
            raise UserError(_("Please fill check list! Or flag this as cash payment"))
        return res

    
    def post(self):
        self.is_checks_fees=False
        self.is_Rejected_Requsted=False
        if(self.transferred_check):
            for record in  self.transferred_checks:
                    record.is_selected_check=False
                    if not record.check_type == 'inbound':
                        raise UserError(_('There is am issued checks in selected list'))
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:
            is_valid = self.isValidChecks()
            if not is_valid:
                raise UserError(_("Please fill check list! Or flag this as cash payment"))
            if rec.state != 'draft':
                raise UserError(
                    _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)
            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))
            # Use the right sequence to set the name
            if rec.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if rec.partner_type == 'customer':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if rec.partner_type == 'supplier':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
                if rec.partner_type == 'employee':
                    if rec.payment_type == 'inbound':
                        sequence_code = 'account.payment.employee.invoice'
                    if rec.payment_type == 'outbound':
                        sequence_code = 'account.payment.employee.refund'
            for each in self.transferred_checks:

                each.is_selected_check=False
            rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.date).next_by_code(sequence_code)
            # Create the journal entry

            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if self.payment_type == 'inbound':
                if self.payment_method_code != 'check_printing':
                    if rec.payment_type == 'transfer':
                        transfer_credit_aml = move.line_ids.filtered(
                            lambda r: r.account_id == rec.company_id.transfer_account_id)
                        transfer_debit_aml = rec._create_transfer_entry(amount)
                        (transfer_credit_aml + transfer_debit_aml).reconcile()

                    rec.write({'state': 'posted', 'move_name': move.name})
                else:
                    rec.write({'state': 'waiting'})
            else:
                for record in  self.transferred_checks:
                    record.is_selected_check=False
                if rec.payment_type == 'transfer':
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()

                rec.write({'state': 'posted', 'move_name': move.name})
                #update checks
                if(self.transferred_check):
                    for record in  self.transferred_checks:
                        if record.check_type == 'inbound':
                            record.vendor_id = self.partner_id[0].id
                            record.state = 'transfer_to_vendor'
                            #record.check_type = 'outbound'
                            checks_log_obj = self.env['receive.check.log']
                            rec = {'state':'transfer_to_vendor', 'transaction':'Transfer to ' + str(self.partner_id[0].name.encode('utf-8')), 'date':fields.Date.today(), 'check_paid_id':record.id}
                            checks_log_obj.create(rec)
                        else:
                          raise UserError(_("These are Issued Checks."))

    @api.onchange('checks_paid', 'transferred_checks')
    def onchange_checks_paid(self):
        amount = 0
        if self.checks_paid:
            for records in self.checks_paid:
                amount += records.amount
        if self.transferred_checks:
            for records in self.transferred_checks:
                amount += records.amount
        self.amount = amount
        for each in self.transferred_checks:
            each.is_selected_check=True


    @api.onchange('transferred_checks')
    def onchange_checks_transferred_checks(self):
        for each in self.transferred_checks:
            each.is_selected_check=False

#     @api.constrains('checks_paid')
#     def constrains_checks_paid(self):
#         bal_amt = 0
#         if self.checks_paid:
#             for records in self.checks_paid:
#                 bal_amt += records.amount
#             if bal_amt != self.amount:
#                 raise UserError(_('Total amount does not match Sum of checks paid!'))


class WizardPayment(models.Model):
    _name = 'wizard.payment'

    payment_journal = fields.Many2one('account.journal', string='Payment Journal', required=1)

    
    def create_payment(self):
        now = datetime.now()
        context = self._context
        check_obj = self.env['checks.paid'].search([('id', '=', context.get('differed_check'))])
        date = now.strftime("%Y-%m-%d")
        account_id_cr = self.env.ref('deferred_checks.rejected_check_erpsmart')
        account_id_db = self.payment_journal
        account_val = 0
        db_account_val = 1
        check_obj.create_journal_entry(date, account_id_cr, account_id_db, account_val, db_account_val)
        check_obj.state = 'success'


class ChecksManager(models.Model):
    _name = 'checks.paid'
    _description = 'Checks'
    #state_tmp= fields.Char(string="state tmp")
    is_checks_fees=fields.Boolean(string =" is have checks fees")
    is_Rejected_Requsted=fields.Boolean(string =" is have Rejected Requsted")

    
    def create_journal_entry(self, check_date, account_id_cr, account_id_db, account_val, db_account_val):
        currency_id = self.payment_form.currency_id if self.payment_form else self.currency_id
        company_currency = self.env.user.company_id.currency_id
        if self.payment_form:
            journal = self.payment_form.journal_id
        else:
            journal = self.env['account.journal'].search([('type','=','bank'),('code','ilike','chk%'),('currency_id','in',[currency_id.id,False] if currency_id == company_currency else [currency_id.id,])], limit=1)#self.env.ref('deferred_checks.check_journal')
        name = self.payment_form.move_name or journal.with_context(
            ir_sequence_date=check_date).sequence_id.next_by_id()
        if self.is_checks_fees:
            name=name.replace('CHK32','FEES')

        move_vals = {
            'name': name,
            'date': check_date,
            'ref': self.payment_form.communication or '',
            'company_id': self.payment_form.company_id.id,
            'journal_id': journal.id,
        }
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        invoice_currency = False
        if self.payment_form.invoice_ids and all(
                [x.currency_id == self.payment_form.invoice_ids[0].currency_id for x in self.payment_form.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.payment_form.invoice_ids[0].currency_id
        move = self.env['account.move'].create(move_vals)
        if not currency_id != self.env.user.company_id.currency_id:
            amount_currency = 0
#         debit, credit, amount_currency, currency_id = aml_obj.with_context(
#             date=check_date).compute_amount_fields(self.amount, self.payment_form.currency_id,
#                                                       self.payment_form.company_id.currency_id, invoice_currency)

        amount_tmp=self.amount
        if self.is_checks_fees:
            currency_id = self.env.user.company_id.currency_id
            if self.is_Rejected_Requsted:
                fees_amount= self.env['product.template'].search([('item_no','=',"FeesCustomerRequest")],limit=1)
                self.amount=fees_amount.list_price
            else:
                fees_amount= self.env['product.template'].search([('item_no','=',"Fees")],limit=1)
                self.amount=fees_amount.list_price
        if self.payment_form:
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=check_date).compute_amount_fields(self.amount, currency_id,
                                                                self.env.user.company_id.currency_id, invoice_currency)
        else:
            if self.is_checks_fees:

                self.currency_id=self.env.user.company_id.currency_id
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=check_date).compute_amount_fields(self.amount, self.currency_id,
                                                                self.env.user.company_id.currency_id, self.env.user.company_id.currency_id)
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
#         if self.payment_form:
        vals = self._get_counterpart_move_line_vals(account_id_db, db_account_val, self.payment_form.invoice_ids)
        counterpart_aml_dict.update(vals)
        counterpart_aml_dict.update({'currency_id': currency_id})
        if(not vals['journal_id']):
            counterpart_aml_dict.update({'journal_id': journal.id})
        #counterpart_aml_dict.update({'check_state': self.state})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
#         if self.payment_form:
        vals = self._get_liquidity_move_line_vals(-self.amount, check_date, account_id_cr, account_val)
        liquidity_aml_dict.update(vals)
        if(not vals['journal_id']):
            liquidity_aml_dict.update({'journal_id': journal.id})
        #liquidity_aml_dict.update({'check_state': self.state})
        liquidity_aml = aml_obj.create(liquidity_aml_dict)
        self.update({'move_line_ids': [counterpart_aml.id, liquidity_aml.id]})
        move.post()
        self.amount=amount_tmp
        #move_ids = [move, counterpart_aml, liquidity_aml]
        #self.store_check_state(move_ids)
        return [move, counterpart_aml, liquidity_aml]

    def store_check_state(self, move_id):
        for move_line in move_id[1:]:
            move_line.check_state = self.state
            move_line.check_id = self.id
            if move_line.check_id.is_checks_fees:
                move_line.is_checks_fees=True
            else:
                move_line.is_checks_fees=False


    def _get_liquidity_move_line_vals(self, amount, check_date, account_id_cr, account_val):
        name = self.payment_form.name
        currency_id = self.payment_form.currency_id if self.payment_form else self.currency_id
        if self.payment_form.payment_type == 'transfer':
            name = _('Transfer to %s') % self.payment_form.destination_journal_id.name
        if account_val == 1:
            vals = {
                'name': name or 'Liquidity Account',
                'account_id': self.payment_form.payment_type in ('outbound',
                                                    'transfer') and account_id_cr.default_debit_account_id.id or account_id_cr.default_credit_account_id.id,
                'payment_id': self.payment_form.id,
                'journal_id': self.payment_form.journal_id.id,
                'currency_id': currency_id != self.payment_form.company_id.currency_id and currency_id.id or False,
                'internal_note': self.state,
            }
        elif account_val == 0:
            vals = {
                'name': name  or 'Liquidity Account',
                'account_id': account_id_cr.id,
                'payment_id': self.payment_form.id,
                'journal_id': self.payment_form.journal_id.id,
                'currency_id': currency_id != self.payment_form.company_id.currency_id and currency_id.id or False,
                'internal_note': self.state,
            }

        # If the journal has a currency specified, the journal item need to be expressed in this currency
        if self.payment_form.journal_id.currency_id and currency_id != self.payment_form.journal_id.currency_id:
            amount = currency_id.with_context(date=check_date).compute(amount, self.payment_form.journal_id.currency_id)
            debit, credit, amount_currency, dummy = self.env['account.move.line'].with_context(
                date=check_date).compute_amount_fields(amount, self.payment_form.journal_id.currency_id,
                                                              self.payment_form.company_id.currency_id)
            vals.update({
                'amount_currency': amount_currency,
                'currency_id': self.payment_form.journal_id.currency_id.id,
            })

        return vals

    def _get_counterpart_move_line_vals(self, account_id_db, db_account_val, invoice=False,):
        currency_id = self.payment_form.currency_id if self.payment_form else self.currency_id
        if self.payment_form.payment_type == 'transfer':
            name = self.payment_form.name
        else:
            name = ''
            if self.payment_form.partner_type == 'customer':
                if self.payment_form.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_form.payment_type == 'outbound':
                    name += _("Customer Refund")
            elif self.payment_form.partner_type == 'supplier':
                if self.payment_form.payment_type == 'inbound':
                    name += _("Vendor Refund")
                elif self.payment_form.payment_type == 'outbound':
                    name += _("Vendor Payment")
            elif self.payment_form.partner_type == 'employee':
                if self.payment_form.payment_type == 'inbound':
                    name += _("Employee Payment")
                elif self.payment_form.payment_type == 'outbound':
                    name += _("Employee Refund")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name) - 2]
        if db_account_val == 0:
            return {
                'name': name or 'Debit Account',
                'account_id': account_id_db.default_debit_account_id.id, #default debit
                'journal_id': self.payment_form.journal_id.id,
                'currency_id': currency_id != self.payment_form.company_id.currency_id and currency_id.id or False,
                'payment_id': self.payment_form.id,
                'internal_note': self.state,
            }
        elif db_account_val == 1:
                return {
                    'name': name or 'Debit Account',
                    'account_id': account_id_db.id,
                    'journal_id': self.payment_form.journal_id.id,
                    'currency_id': currency_id != self.payment_form.company_id.currency_id and currency_id.id or False,
                    'payment_id': self.payment_form.id,
                    'internal_note': self.state,
                }

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """

        if self.payment_form:

            partner_id =self.check_type in ('inbound', 'outbound') and self.state =='transfer_to_vendor' and len(self.vendor_id) > 0 and self.env['res.partner'].search([('id','=',self.vendor_id.id)]) or False

            return {
                'partner_id': (partner_id and self.env['res.partner']._find_accounting_partner(partner_id).id) or (self.payment_form.payment_type in ('inbound', 'outbound') and
                              self.env['res.partner']._find_accounting_partner(self.payment_form.partner_id).id or False),
                'invoice_id': invoice_id and invoice_id.id or False,
                'move_id': move_id,
                'debit': debit,
                'credit': credit,
                'amount_currency': amount_currency or False,
                'internal_note': self.state,
            }
        else:

            partner_id =self.check_type in ('inbound', 'outbound') and self.state =='transfer_to_vendor' and len(self.vendor_id) > 0 and self.env['res.partner'].search([('id','=',self.vendor_id.id)]) or False

            return {
            'partner_id':(partner_id and self.env['res.partner']._find_accounting_partner(partner_id).id) or (self.check_type in ('inbound', 'outbound') and self.check_type in ('inbound', 'outbound') and
                          self.env['res.partner']._find_accounting_partner(self.issuer_names).id or False),
            'invoice_id': invoice_id and invoice_id.id or False,
            'move_id': move_id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'internal_note': self.state,
        }

    
    def transfer_check(self):

        if not self.transfer_bank:
            raise UserError(_('Select Bank For Transfer Check'))



        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        #self.deposit_date = now.strftime("%Y-%m-%d")

        self.transfer_date = operation_id.date_transaction
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        self.state = 'transferred'
        account_id_cr = self.env.ref('deferred_checks.check_box_erpsmart')
        user_account = self.transfer_user_bank #self.transfer_bank

        #if self.payment_form:
        #    account_id_cr = self.payment_form.journal_id
        #credit always jernal
        #get currency
        default_currency = self.env.user.company_id.currency_id
        payment_currency = self.payment_form.currency_id if self.payment_form else self.currency_id
        payment_currency_id = payment_currency.id
        payment_currency_name = payment_currency.name


        #check if bank currency
        if(payment_currency_id and payment_currency != default_currency):
            #try to catch undercollection account and diposit check with this currency
            code = "CB"
            #must be reviewed
            account_id_cr=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
            if(not account_id_cr):
                raise UserError('While trying to transfer check (%s) can not find check box account with %s currency'%(self.name,payment_currency_name,))
            #code = "UC"
            #account_id_db=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
            #if(not account_id_db):
            #    raise UserError('While trying to transfer check (%s) can not find under collection checks account with %s currency'%(self.name,payment_currency_name,))    
        account_from_journal = self.env['account.journal'].search([('bank_account_id','=',user_account[0].id)], limit=1)
        #if(account_from_journal.default_credit_account_id):
        #    account_from_journal = account_from_journal.default_credit_account_id
        account_id_db = self.transfer_bank
        if(account_from_journal.default_debit_account_id):
            account_id_db = account_from_journal.default_debit_account_id
        else:
            raise UserError(_('Choosed Account can not be debit account'))
        account_val = 0
        db_account_val = 1

        move_id = self.create_journal_entry(self.transfer_date, account_id_cr, account_id_db, account_val, db_account_val)
        self.store_check_state(move_id)
        checks_log_obj = self.env['receive.check.log']
        rec = {'state':'transferred', 'transaction':'Transfer to ' + self.transfer_bank.name, 'date':self.transfer_date ,'creation_date':fields.Date.today(), 'check_paid_id':self.id}
        checks_log_obj.create(rec)

    
    def deposit_check(self):
        if not self.deposit_accnt:
            raise UserError(_('Enter Account No For Deposit Check'))

        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        #self.deposit_date = now.strftime("%Y-%m-%d")
        self.deposit_date = operation_id.date_transaction
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        check_date = self.due_date
        if(check_date > self.deposit_date):
            raise UserError(_("You can not deposit check before it's due date"))
        #transferred
        user_account = self.transfer_user_bank #self.transfer_bank
        if(self.state == 'transferred'):
            account_from_journal = self.env['account.journal'].search([('bank_account_id','=',user_account[0].id)], limit=1)
            cr_account = None
            if(account_from_journal.default_credit_account_id):
                cr_account = account_from_journal.default_credit_account_id
            else:
                raise UserError('Please check cridit account  to trasfered bank to check (%s)'%(self.name,))
        else:
            #get account of checkbox with the same currency
            payment_currency = self.payment_form.currency_id if self.payment_form else self.currency_id #USD, ILS , ....
            payment_currency_id = payment_currency.id
            payment_currency_name = payment_currency.name
            #make sure it's not default one
            default_currency = self.env.user.company_id.currency_id.id
            if(not payment_currency_id or default_currency == payment_currency_id):
                cr_account = self.env.ref('deferred_checks.check_box_erpsmart')
            else:
                expected_code = "CB"
                cr_account=self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if(not cr_account):
                    raise UserError('You do not have checkbox account with %s currency'%(payment_currency_name,))

        account_from_journal = self.env['account.journal'].search([('bank_account_id','=',self.deposit_usr_account[0].id)], limit=1)

        if(account_from_journal.default_debit_account_id):
            account_from_journal = account_from_journal.default_debit_account_id
        else:
            raise UserError(_('Choosed Account can not be debit account'))



        account_id_cr = cr_account
        account_id_db = account_from_journal #self.env.ref('deferred_checks.dipositess_check_erpsmart')
        account_val = 0
        db_account_val = 1
        move_id = self.create_journal_entry(self.deposit_date, account_id_cr, account_id_db, account_val, db_account_val)
        self.state = 'success'
        self.store_check_state(move_id)
        flag = 0
        updated_amount = 0
        for each in self.payment_form.checks_paid:
            if each.state != 'success' and each.state != 'returned': # and state != 'rejected'
                flag = 0
                break
            else:
                if each.state == 'success':
                    updated_amount = updated_amount + each.amount
                flag = 1
        if flag == 1:
            self.payment_form.write({'amount': updated_amount,
                                     'state': 'posted'})
        checks_log_obj = self.env['receive.check.log']
        rec = {'state':'success', 'transaction':'Success Fully Deposited to Account :-' + self.deposit_accnt.name,'date':self.deposit_date ,'creation_date':fields.Date.today(), 'check_paid_id':self.id}
        checks_log_obj.create(rec)





    
    def redeposit_check(self):
        each = self
        #get check currency
        ##undercollection = self.env.ref('deferred_checks.differed_check_erpsmart') # deb
        rejectedcheck = self.env.ref('deferred_checks.rejected_check_erpsmart') # cridit
        frompayment = each.payment_form
        #get by currency
        default_currency = self.env.user.company_id.currency_id
        if(frompayment): # from payment
            payment_currency = frompayment.currency_id
            payment_currency_id = payment_currency.id
            payment_currency_name = payment_currency.name
            if(payment_currency_id and payment_currency != default_currency):
                #try to catch undercollection account and diposit check with this currency
                ##code = "UC"
                #must be reviewed
                ##undercollection=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
               ##if(not undercollection):
                ##    raise UserError('While trying to deposit check (%s) can not find under collection checks account with %s currency'%(each.name,payment_currency_name,))
                code = "RC"
                rejectedcheck=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if(not rejectedcheck):
                    raise UserError('While trying to deposit check (%s) can not find rejected checks account with %s currency'%(each.name,payment_currency_name,))

        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        #self.deposit_date = now.strftime("%Y-%m-%d")
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        each.deposit_date = operation_id.date_transaction
        check_date = self.due_date
        if(check_date > self.deposit_date):
            raise UserError(_("You can not deposit check before it's due date"))


        account_from_journal = self.env['account.journal'].search([('bank_account_id','=',self.deposit_usr_account[0].id)], limit=1)
        #if(account_from_journal.default_credit_account_id):
        #    account_from_journal = account_from_journal.default_credit_account_id
        if(account_from_journal.default_debit_account_id):
            account_from_journal = account_from_journal.default_debit_account_id
        else:
            raise UserError(_('Choosed Account can not be debit account'))


        account_val = 0
        db_account_val = 1
        account_id_cr = rejectedcheck
        account_id_db = account_from_journal
        move_id = each.create_journal_entry(each.deposit_date, account_id_cr, account_id_db, account_val, db_account_val)
        self.store_check_state(move_id)
        each.state = 'success'
        flag = 0
        updated_amount = 0
        for each2 in each.payment_form.checks_paid:
            if each2.state != 'success' and each2.state != 'returned':
                flag = 0
                break
            else:
                if each2.state == 'success':
                    updated_amount = updated_amount + each2.amount
                flag = 1
        if flag == 1:
            each.payment_form.write({'amount': updated_amount,
                                    'state': 'posted'})
        checks_log_obj = self.env['receive.check.log']

        rec = {'state':'success', 'transaction':'Success Fully ReDeposited to Account :-' + account_id_db.name, 'date':self.deposit_date , 'creation_date':fields.Date.today(), 'check_paid_id':each.id}
        checks_log_obj.create(rec)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move_id[0].id,
            }








    
    def reject_check(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        #self.deposit_date = now.strftime("%Y-%m-%d")
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        rejected_date =operation_id.date_transaction
        #get account of differed checks with the same currency
        payment_currency = self.payment_form.currency_id if self.payment_form else self.currency_id #USD, ILS , ....
        payment_currency_id = payment_currency.id
        payment_currency_name = payment_currency.name
        #make sure it's not default one
        default_currency = self.env.user.company_id.currency_id.id

        if(self.state == 'issue'):
            if self.payment_form:
                debit = self.payment_form.journal_id.default_debit_account_id #self.env['account.journal'].search([('bank_account_id', '=', self.withdraw_user_account[0].id)], limit=1).default_debit_account_id
            elif self.deposited_journal:
                debit = self.deposited_journal.default_debit_account_id
            else:
                raise UserError('Check with number (%s) has no payment or deposit journal'%(self.name,))
        else:
        #if(not self.state == 'success'):
        #    raise UserError(_('Check with number (%s) have not be deposted'%(self.name,)))
            if(not payment_currency_id or default_currency == payment_currency_id):
                #undercollection = self.env.ref('deferred_checks.differed_check_erpsmart')
                debit = self.env.ref('deferred_checks.rejected_check_erpsmart')
            else:
                #expected_code = "UC"
                #undercollection = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                #if(not undercollection):
                #    raise UserError('You do not have under collection account with %s currency'%(payment_currency_name,))

                expected_code = "RC"
                debit = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if(not debit):
                    raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))
        if(self.state == 'success'):
            undercollection = self.env['account.journal'].search([('bank_account_id','=',self.deposit_usr_account[0].id)], limit=1)
            account_val = 1
        elif(self.state == 'transfer_to_vendor'):
            undercollection = self.env['account.account'].search([('code','=','111100')], limit=1) #account payable
            account_val = 0
        elif(self.state == 'transferred'):
            if self.transfer_user_bank:
                undercollection = self.env['account.journal'].search([('bank_account_id','=',self.transfer_user_bank[0].id)], limit=1)
            else:
                undercollection = self.transfer_bank
            account_val = 1
        elif(self.state == 'issue'):
            undercollection = self.env['account.account'].search([('code','=','111100')], limit=1) #account payable
            account_val = 0
        else:
            raise UserError('Can not reject this type of checks')

        db_account_val = 1
        account_id_cr = undercollection
        account_id_db = debit
        if(not account_id_db):
            raise UserError('There is no debit account with this user bank account')


        move_id = self.create_journal_entry(rejected_date, account_id_cr, account_id_db, account_val, db_account_val)
        checks_log_obj = self.env['receive.check.log']
        if(self.state != 'issue'):
            self.check_type = 'inbound'
        self.state = 'rejected'
        self.store_check_state(move_id)
        rec = {'state':'returned' if(self.state == 'issue') else 'rejected', 'transaction':'Returned' if(self.state == 'issue') else 'Rejected','creation_date':fields.Date.today(), 'date':rejected_date, 'check_paid_id':self.id}
        checks_log_obj.create(rec)
        return {'cridit': undercollection , 'debit': debit}










    
    def back_to_origin(self, checked = True):
        state_tmp= ""


        each = self
        if (each.state in ["transferred"] ):
            #each.is_checks_fees=True
            state_tmp= "transferred"




        if not each.state in ('success','transferred','rejected','received'):
            raise UserError(_('Check with number (%s) can not be back to origin'%(each.name,)))
        if(each.state not in ('rejected', 'received') and checked):
              # state not in ('rejected', 'recieved')
            each.reject_check() #reject check
        payment_currency = self.payment_form.currency_id if self.payment_form else self.currency_id #USD, ILS , ....
        payment_currency_id = payment_currency.id
        payment_currency_name = payment_currency.name
        default_currency = self.env.user.company_id.currency_id.id
        #if(not self.state == 'success'):
        #    raise UserError(_('Check with number (%s) have not be deposted'%(self.name,)))
        account_val = 0
        db_account_val = 1
        if (each.state == 'rejected'):
            if(not payment_currency_id or default_currency == payment_currency_id):
                #undercollection = self.env.ref('deferred_checks.differed_check_erpsmart')
                cridit_account = self.env.ref('deferred_checks.rejected_check_erpsmart')
            else:
                expected_code = "RC"
                cridit_account = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if(not cridit_account):
                    raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))
            #from rejected check to account receivable
            '''
            cridit = rejectedcheck #rejected check
            debit = self.env['account.account'].search([('code', '=', '101200')],limit=1)
            now = datetime.now()
            each.deposit_date = now.strftime("%Y-%m-%d")
            
            account_val = 0
            db_account_val = 1
            each.create_journal_entry(each.deposit_date, cridit, debit,account_val,db_account_val)
            each.state = 'backtoorigin'
            checks_log_obj = self.env['receive.check.log']
            rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN', 'date':fields.Date.today(), 'check_paid_id':each.id}
            checks_log_obj.create(rec) 
            '''
        elif (each.state == 'received' ):
            if(not payment_currency_id or default_currency == payment_currency_id):
                #undercollection = self.env.ref('deferred_checks.differed_check_erpsmart')
                cridit_account = self.env.ref('deferred_checks.check_box_erpsmart')
            else:
                expected_code = "CB" #cridit = ...payment.journal_id
                cridit_account = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)

                if(not cridit_account):
                    raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))
            #from rejected check to account receivable
        elif(each.state == 'transferred'):
            cridit_account = self.env['account.journal'].search([('bank_account_id','=',self.transfer_user_bank[0].id)], limit=1)
            account_val = 1
            if(not cridit_account):
                raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))
        else:
            return
        cridit = cridit_account
        debit = self.env['account.account'].search([('code', '=', '101200')],limit=1) #each.payment_form.
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        each.deposit_date = operation_id.date_transaction

        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))


        move_id = each.create_journal_entry(each.deposit_date, cridit, debit,account_val,db_account_val)

        each.state = 'backtoorigin'
        self.store_check_state(move_id)
        checks_log_obj = self.env['receive.check.log']
        rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN','date':each.deposit_date, 'creation_date':fields.Date.today(), 'check_paid_id':each.id}
        checks_log_obj.create(rec)
        if (state_tmp=="transferred"):
            debit = self.env['account.account'].search([('code', '=', '101200')],limit=1) #each.payment_form.
            expected_code = "RCF"
            cridit_account = self.env['account.account'].search([('code','like',expected_code+"%")], limit=1)
            if(not cridit_account):
                raise UserError("You do not have rejected checks fee's account with %s currency"%(payment_currency_name,))

            account_val = 0
            db_account_val = 1

            if not checked:
                each.is_Rejected_Requsted=True

            else :
                each.is_Rejected_Requsted=False
            each.is_checks_fees=True

            move_id = each.create_journal_entry(each.deposit_date, cridit_account, debit,account_val,db_account_val)

            self.store_check_state(move_id)
            each.is_checks_fees=False
            checks_log_obj = self.env['receive.check.log']
            #rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN', 'date':fields.Date.today(), 'check_paid_id':each.id}
            #checks_log_obj.create(rec)


        return True







    
    def permanent_reject(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        return_date = operation_id.date_transaction
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))


        account_id_cr = self.env.ref('deferred_checks.rejected_check_erpsmart')
        account_id_db = self.payment_form.destination_account_id
        account_val = 0
        db_account_val = 0
        move_id = self.create_journal_entry(return_date, account_id_cr, account_id_db, account_val, db_account_val)
        self.state = 'returned'
        self.store_check_state(move_id)
        checks_log_obj = self.env['receive.check.log']
        rec = {'state':'returned', 'transaction':'returned','date': return_date , 'creation_date':fields.Date.today(), 'check_paid_id':self.id}
        checks_log_obj.create(rec)

    
    def withdraw_check(self):

        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        return_date = operation_id.date_transaction
        now = datetime.now()
        if operation_id.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        '''
        if self.payment_form:
            account_id_cr = self.payment_form.journal_id
        else:
            account_id_cr = self.env.ref('deferred_checks.check_box_erpsmart')

        account_id_db = self.env.ref('deferred_checks.rejected_check_erpsmart')
        '''
        if self.payment_form:
            account_id_db = self.payment_form.journal_id.default_debit_account_id
        elif self.deposited_journal:
            account_id_db = self.deposited_journal.default_debit_account_id
        else:
            raise UserError('Check with number (%s) has no payment or deposit journal'%(self.name,))
        account_id_cr = self.env['account.journal'].search([('bank_account_id','=',self.withdraw_user_account[0].id)], limit=1)
        if account_id_cr:
            account_id_cr_account = account_id_cr.default_credit_account_id
        account_val = 0
        db_account_val = 1
        move_id = self.create_journal_entry(return_date, account_id_cr_account, account_id_db, account_val, db_account_val)
        self.state = 'withdraw_from_bank'
        self.store_check_state(move_id)
        checks_log_obj = self.env['receive.check.log']
        rec = {'state':'withdraw_from_bank', 'transaction':'Success Fully Withdraw  :-' + self.transfer_bank.name, 'date': return_date , 'creation_date':fields.Date.today(), 'check_paid_id':self.id}
        checks_log_obj.create(rec)


#     company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    payment_form = fields.Many2one('account.payment', string='Related Payment')
    currency_id = fields.Many2one('res.currency','Currency',store=True, related="payment_form.currency_id")
    received_date = fields.Date(string='Received Date', related='payment_form.date', store=True)
    name = fields.Char(string='Check Number',default=lambda self:self.ch_number)
#     bank_account = fields.Many2one('res.bank', string='Bank', required=1,related='bank_account_rel')
    bank_account = fields.Many2one('res.bank', string='Bank Account', required=1)
    bank_name = fields.Char(string='Bank Name', related='bank_account.name', readonly=1, store=True)
#     branch_no = fields.Char(string='Branch No',related='branch_no_rel')
    branch_no = fields.Char(string='Branch No')
#     branch_name = fields.Char(string='Branch Name',related='branch_name_rel')
    branch_name = fields.Char(string='Branch Name')
    due_date = fields.Date(string='Due Date', required=1, default=datetime.today() + relativedelta(months=1))
    amount = fields.Float(string='Amount')
    transfer_bank = fields.Many2one('res.bank', string='Transferred Bank')
    transfer_user_bank = fields.Many2one('res.partner.bank','Transferred User Account')
    deposit_accnt = fields.Many2one('res.bank', string="Deposit Account")
    deposit_usr_account = fields.Many2one('res.partner.bank','Deposit User Account')
    withdraw_user_account = fields.Many2one('res.partner.bank','Withdraw User Account')
    received_date = fields.Date(string='Received Date', related='payment_form.date', store=True)

    issuer_names = fields.Many2one('res.partner', string='Payment Issuer Name', related='payment_form.partner_id', store=True)
    # issuer_name = fields.Char(string='Issuer Name', related='issuer_names.name')
    # issuer_names = fields.Many2one('res.partner', string='Issuer Name')
    issuer_name = fields.Char(string='Issuer Name')
    note = fields.Text(string='Note')
    state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('transfer_to_vendor', 'Transferred To Vendor'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('drawcash','Draw Cash'),
                              ('issue', 'Issued Deferred')], string='State')
    states = fields.Selection([('received', 'Received'),
                               ('withdraw_from_bank', 'Withdraw From Bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('transfer_to_vendor', 'Transferred To Vendor'),
                              ('drawcash','Draw Cash'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('issue', 'Issued Deferred')], string='Related State', related='state')

    transfer_date = fields.Date(string='Transfer Date')
    deposit_date = fields.Date(string='Deposited Date')
    reject_date = fields.Date(string='Reject Date')
    deposited_journal = fields.Many2one('account.journal', string='Deposited Journal', required=True,
                                        domain=[('type', 'in', ('cash', 'bank'))],
                                        default=lambda self: self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))], limit=1))

    check_type = fields.Selection([('inbound', 'Received Check'),
                                   ('outbound', 'Issued Check'),
                                   ('transfer', 'Transferred Check')], string='Type of Check',
                                  )
    check_type_test = fields.Selection([('inbound', 'Received Check'),
                                        ('outbound', 'Issued Check'),
                                        ('transfer', 'Transferred Check')], #string='Payment Type of Check',
                                       related='payment_form.payment_type')
    move_line_ids = fields.Many2many('account.move.line', 'check_account_move_line_rel')
    customer_bank_acc = fields.Char(string='Customer Bank Account')
    ch_number = fields.Char(related='payment_form.check_number')

    customer_bank_acc_rel = fields.Char(string=' Payment Customer Bank Account', related='payment_form.customer_bank_acc')
    bank_account_rel = fields.Many2one('res.bank', required=0, related='payment_form.bank_account')
    branch_no_rel = fields.Char(related='payment_form.branch_no',string='Payment Branch No' )
    branch_name_rel = fields.Char(string='Payment Branch Name', related='payment_form.branch_name')
    due_date_rel = fields.Date(string=' Payment Due Date', related='payment_form.due_date')
    ch_amount = fields.Float(related='payment_form.ch_amount')
    receive_checks = fields.One2many('receive.check.log', 'check_paid_id', string="Receive Check State")
    payment_type = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound')], string='payment_type', store=True, related='payment_form.payment_type')



    
    def unlink(self):
        for ckeck in self:
            if ckeck.check_type == 'inbound' and ckeck.state != 'received':
                raise Warning(_('Can not delete ckeck (%s) there is some moves related to it.'%ckeck.name))
            elif ckeck.check_type == 'outbound' and ckeck.state != 'issue':
                raise Warning(_('Can not delete ckeck (%s) there is some moves related to it.'%ckeck.name))
        return super(ChecksManager,self).unlink()
    @api.model
    def search_read(self,domain=None,fields=None,offset=0,limit=None, order=None):

        domain2=domain

        ors = []
        i = 0
        d =  0
        fields2 = ['due_date','amount', 'bank_name','issuer_names.name']

        while (d <len(domain)):

            length = len(fields2)
            if( domain[d][0] == 'name' ):

                name = domain[d][2]

                domain3= []
                name='%'+'%'.join(name.split())+'%'
                for f in fields2:
                    if(f == 'due_date'):
                        #date = datetime.datetime.strptime(name, '%d/%m/%Y').strftime('%d/%m/%y')
                        date= name.split('/')

                        if(len(date)==3):

                            #dd/mm/yyyy
                            try:
                                #print "the date is", date
                                map(int, date) # map all elemets to integer parser
                                database_date = date[2]+'-'+date[1]+'-'+date[0]
                                domain3 += [[u'due_date','ilike',database_date]]
                            except:
                                length -= 1
                        else:
                            length -= 1

                    elif(f == 'amount'):
                        try:
                            amount = float(name)
                            domain3 += [[u'amount','=',amount]]
                        except:
                                length -= 1
                    """
                    else:
                        domain3 += [[f,'ilike',name]]
                    """

                domain2 = domain2[:d] + ['|' for j in range(len(domain3))] + domain3+domain2[d:]

            d = d+1
        return super(ChecksManager, self).search_read(domain=domain2,fields=fields,offset=offset,limit=limit, order=order)

    @api.onchange('bank_account')
    def onchange_bank_account(self):
        if self.bank_account:
            self.branch_no_rel = self.bank_account.branch_number
            self.branch_name_rel = self.bank_account.branch_name
            self.branch_no = self.bank_account.branch_number
            self.branch_name = self.bank_account.branch_name

    @api.onchange('payment_type')
    def onchange_payment_type(self):
        if self.payment_type == 'inbound':
            self.state = 'received'
        elif self.payment_type == 'outbound':
            self.state = 'issue'

    @api.constrains('name', 'customer_bank_acc', 'bank_account', 'branch_no')
    #,'amount')
    def check_validation(self):
        if self.amount <= 0:
            raise ValidationError(_("The following check %s Details must have valid amount (grater than 0)!"%(self.name)))
        each = self.search([('name','=',self.name),('id','!=',self.id),('bank_account','=',self.bank_account.id),('customer_bank_acc','=',self.customer_bank_acc),('branch_no','=',self.branch_no)],limit=1)
        if each:
            raise ValidationError(_("The following check %s details must be unique!"%(each.name)))
    @api.onchange('check_type')
    def onchange_state(self):
        if self.check_type == 'inbound':
            self.state = 'received'
        elif self.check_type == 'outbound':
            self.state = 'issue'
        elif self.check_type == 'transfer':
            self.state = 'transferred'


    @api.onchange('check_type_test')
    def onchange_check_type(self):
        if self.check_type_test == 'inbound':
            self.check_type = 'inbound'
        elif self.check_type_test == 'outbound':
            self.check_type = 'outbound'

    def action_view_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.payment_form.id,
            'target': 'current',
        }

    def action_view_transactions(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.move_line_ids.ids)],
        }
    '''
    @api.onchange('ch_number', 'branch_name_rel', 'branch_no_rel', 'bank_account_rel', 'customer_bank_acc_rel', 'due_date_rel')
    def check_number(self):
        if self.ch_number:
            self.name = self.ch_number
        if self.customer_bank_acc_rel:
            self.customer_bank_acc = self.customer_bank_acc_rel
        if self.bank_account_rel:
            self.bank_account = self.bank_account_rel
        if self.branch_no_rel:
            self.branch_no = self.branch_no_rel
        if self.branch_name_rel:
            self.branch_name = self.branch_name_rel
        if self.due_date_rel:
            self.due_date = datetime.strptime(self.due_date_rel, '%Y-%m-%d') + relativedelta(months=1)
    '''
    @api.model
    def default_get(self,vals):
        checks = self._context.get('c_ids',False)
        res = super(ChecksManager, self).default_get(vals)
        if checks and len(checks)>0:
            last_check = checks[-1][2]
            if last_check:
                res['name'] = str(int(last_check.get('name',0)) + 1)
                res['customer_bank_acc'] = last_check['customer_bank_acc']
                res['bank_account'] = last_check['bank_account']
                res['branch_name'] = last_check['branch_name']
                res['due_date'] = str(datetime.strptime(last_check['due_date'], '%Y-%m-%d') + relativedelta(months=1)).replace(' 00:00:00','')
        return res
    @api.model
    def create(self, values):
        rec = super(ChecksManager, self).create(values)
        list_log = []
        payment_form = '/'
        if rec.payment_form:
            payment_form = rec.payment_form.name
            if rec.payment_form.payment_type == 'inbound':
                list_log.append((0, 0, {'state':'received', 'transaction':payment_form, 'date':fields.Date.today()}))
            if rec.payment_form.payment_type == 'outbound':
                list_log.append((0, 0, {'state':'issue', 'transaction':payment_form, 'date':fields.Date.today()}))
        else:
            if rec.check_type == 'inbound':
                list_log.append((0, 0, {'state':'received', 'transaction':'Draft Payment', 'date':fields.Date.today()}))
            if rec.check_type == 'outbound':
                list_log.append((0, 0, {'state':'issue', 'transaction':'Draft Payment', 'date':fields.Date.today()}))
        rec.receive_checks = list_log
        return rec

# @api.model
#     def create(self, values):
#         rec = super(ChecksManager, self).create(values)
#         list_log = []
#         payment_form = '/'
#         if rec.payment_form:
#             payment_form = rec.payment_form.name
#         if rec.payment_form.payment_type == 'inbound':
#             list_log.append((0, 0, {'state':'received', 'transaction':payment_form, 'date':fields.Date.today()}))
#         if rec.payment_form.payment_type == 'outbound':
#             list_log.append((0, 0, {'state':'issue', 'transaction':payment_form, 'date':fields.Date.today()}))
#         rec.receive_checks = list_log
#         return rec


class ChecksTransferLog(models.Model):
    _name = 'receive.check.log'


    check_paid_id = fields.Many2one('checks.paid', string="Check Paid")
    date = fields.Date(" Transaction Date")
    creation_date = fields.Date(" Creation Date")

    state = fields.Selection([ ('received', 'Received'),
                               ('transferred', 'Transferred'),
                               ('success', 'Success'),
                               ('withdraw_from_bank', 'Withdraw from bank'),
                               ('rejected', 'Rejected'),
                               ('returned', 'Returned'),
                               ('backtoorigin', 'BACK TO ORIGIN'),
                               ('drawcash','Draw Cash'),
                               ('issue', 'Issued Deferred'),
                               ('transfer_to_vendor', 'Transfared To Vendor')], string='State')
    transaction = fields.Char("Transaction Details")

class ChecksTransfer(models.Model):
    _name = 'checks.paid.transfer'

    transfer_bnk = fields.Many2one('res.bank', string="Select Bank for Transfer Check", required=True)

    
    def check_transfer(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['checks.paid'].browse(active_ids):
            if record.check_type == 'inbound':
                if record.state in ('success', 'rejected', 'returned'):
                    raise UserError(_("Selected checks cannot be deposit."))
                elif record.state == 'received':
                    record.transfer_bank = self.transfer_bnk
                    record.transfer_check()
            else:
                raise UserError(
                    _("These are Issued Checks."))
        return {'type': 'ir.actions.act_window_close'}


class ChecksDeposit(models.Model):
    _name = 'checks.paid.deposit'

    transfer_bnk = fields.Many2one('res.bank', string="Select Bank for Transfer Check", required=True)
    accnt_no = fields.Char(string='Account No', required=True)
    deposit_journal = fields.Many2one('account.journal', string='Deposit Journal', required=True,
                                      domain=[('type', 'in', ('cash', 'bank'))],
                                      default=lambda self: self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))], limit=1))

    
    def check_deposit(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['checks.paid'].browse(active_ids):
            if record.payment_form.payment_type == 'inbound':
                if record.state in ('success', 'rejected', 'returned'):
                    raise UserError(
                        _("Selected checks cannot be deposit."))
                elif record.state == 'received':
                    record.transfer_check()
                    record.transfer_bank = self.transfer_bnk
                    record.deposit_accnt = self.accnt_no
                    record.deposited_journal = self.deposit_journal
                    record.deposit_check()
                elif record.state == 'transferred':
                    record.transfer_bank = self.transfer_bnk
                    record.deposit_accnt = self.accnt_no
                    record.deposited_journal = self.deposit_journal
                    record.deposit_check()
            else:
                raise UserError(
                    _("These are Issued Checks."))
        return {'type': 'ir.actions.act_window_close'}


class ChecksReject(models.Model):
    _name = 'checks.paid.reject'

    
    def check_reject(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['checks.paid'].browse(active_ids):
            if record.payment_form.payment_type == 'inbound':
                if record.state in ('success', 'rejected', 'returned'):
                    raise UserError(
                        _("Selected checks cannot be reject."))
                elif record.state == 'received':
                    record.transfer_check()
                    record.reject_check()
                    record.permanent_reject()
                elif record.state == 'transferred':
                    record.reject_check()
                    record.permanent_reject()
            else:
                raise UserError(
                    _("These are Issued Checks."))
        return {'type': 'ir.actions.act_window_close'}
