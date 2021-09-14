# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class CheckOperation(models.Model):
    _name = 'check.operation'
    _racname = 'check_number'

    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled')],
                             readonly=True)
    checks_paid_ids = fields.One2many('check.operation.details', 'operation_id', string='Checks')
    selected_checks_detail_ids = fields.One2many('selected.check.operation.details', 'operation_id', string='Selected Checks')

    
    # state = fields.Selection([('inbound', 'Received'),
    #                           ('withdraw_from_bank', 'Withdraw from bank'),
    #                                    ('outbound', 'Issued'),
    #                                    ('transfer', 'Transferred'),
    #                                     ('confirm', 'Confirm')], string='State'
    #                                   )
    state_search = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('drawcash','Draw Cash'),
                              ('issue', 'Issued Deferred'),
                              ('transfer_to_vendor', 'Transfared To Vendor')], string='State')
                                      

    check_number = fields.Char('Check Number')
    due_date = fields.Date('Due Date')
    check_op_date = fields.Date('Check Operation Date')

    received_date= fields.Date('Received Date')

    bank_id = fields.Many2one('res.bank', string='Bank')
    transfered_bank=fields.Many2one('res.bank', string='Transferred Bank')
    amount = fields.Float('Amount')
    acc_number = fields.Char(string='Account Number')
   
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    vendor_id = fields.Many2one('res.partner', string='Vendor Name')

    issuer_id = fields.Many2one('res.partner', string='Issuer Name')
    check_type = fields.Selection([('inbound', 'Received Check'),
                                   ('outbound', 'Issued Check'),
                                   ('transfer', 'Transferred Check')], string='Type of Check',
                                  )
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user.id)                       
    date_transaction = fields.Date(string='Date of Transaction' , default=datetime.today() )
    
    number_check = fields.Integer('Number of checks', default=lambda self:len(self.selected_checks_detail_ids))
    total_amount = fields.Float('Total amount')
    transfer_bank = fields.Char('Transfer Bank')
    currency_code = fields.Many2one('res.currency','Currency')
    select_all = fields.Boolean(string='Select all')
    admin_check_field = fields.Boolean('Check', compute='get_user_group')
    
      
    @api.depends('check_number')
    def get_user_group(self):
        
        if (self.env.user.id == 10) or (self.env.user.id==1):
           self.admin_check_field = True 
        else :
            self.admin_check_field = False


    @api.onchange('select_all')
    def select_all_checks(self):
        if self.select_all == True:
            for each in self.checks_paid_ids:
                each.selected_check = True
        else:
            for each in self.checks_paid_ids:
                each.selected_check = False
                   
    
    def add_to_selected_list(self):
        if(len(self.checks_paid_ids)): # check types
            current = None or (len(self.selected_checks_detail_ids) > 0 and self.selected_checks_detail_ids[0].state) # if there is selected checks
            for each in self.checks_paid_ids:
                if each.selected_check:
                    if not current: # first selected
                        current = each.state 
                    elif each.state != current:    
                        raise UserError(_('Make sure that all selected ckeckes have same state'))
                        return
                
        for each in self.checks_paid_ids:
            if each.selected_check:
                selected_id = self.write({'selected_checks_detail_ids':[(0, 0, {'check_name':each.check_name,
                                            'acc_number':each.checks_id.customer_bank_acc,
                                            'due_date':each.due_date,
                                            'received_date':each.received_date,

                                            'issuer_names':each.issuer_names.id,
                                            'issuer_display_names':each.issuer_display_names,

                                            'branch_name':each.branch_name,
                                            'bank_id':each.bank_id.id,
                                            'state':each.state,
                                            'operation_id':each.operation_id.id,
                                            'amount':each.amount,
                                            'check_op_id':each.id,
                                            'checks_id':each.checks_id.id,
                                            'currency_code':each.currency_code.id,})]
                                            })
                each.unlink()
        count = 0
        total = 0
        for each in self.selected_checks_detail_ids:
            count += 1
            total += (each.amount * each.currency_code.rate)
        self.total_amount = total 
        self.number_check = count
        self.select_all = False

    def act_confirm(self):
        self.state = "confirm"

    def unlink(self):
        for rec in self:
            if rec.state == "confirm":
                raise UserError(_('You Can Not Delete.'))

        rec = super(CheckOperation, self).unlink()
        return rec

    
    def write(self, values):
        if self.state == "confirm":
                raise UserError(_('You Can Not Edit On this Confirm Stage'))
        return super(CheckOperation, self).write(values)

    
    def search_check_data(self):

        domain = [('check_type', '=', 'inbound')]
        check_list = []
        if self.checks_paid_ids:
            self.checks_paid_ids = None
        if self.vendor_id:
            domain += [('vendor_id', '=', self.vendor_id.id)]
        if self.check_number:
            domain += [('name', 'ilike', '%'+self.check_number+'%')]
        if self.acc_number:
            domain += [('customer_bank_acc', 'ilike', '%'+self.acc_number+'%')]
        if self.due_date:
            domain += [('due_date', '=', self.due_date)]
        if self.received_date:
            domain += [('received_date', '=', self.received_date)]
        if self.bank_id:
            domain += [('bank_account', '=', self.bank_id.id)]
        if self.amount:
            domain += [('amount', '=', self.amount)]
  
        if self.issuer_id:
            domain += [('issuer_names', '=', self.issuer_id.id)]
        if self.vendor_id:
            domain += [('vendor_id', '=', self.vendor_id.id)]
        if self.acc_number:
            domain += [('customer_bank_acc', 'ilike', '%'+self.acc_number+'%')]
        if self.state_search:
            domain += [('state','=',self.state_search)]
        if self.transfered_bank:
            domain += [('transfer_bank','=',self.transfered_bank.id)]
        if domain:
            check_ids = self.env['checks.paid'].search(domain)
            for each in check_ids:
                check_list += [(0, 0, {'check_name':each.name,
                                        'acc_number':each.customer_bank_acc,
                                        'due_date':each.due_date,

                                        'received_date':each.received_date,
                                        #'transfer_bank': each.transfer_bank.id,

                                        'issuer_names':each.issuer_names.id,
                                        'issuer_display_names':each.issuer_name,
                                        'branch_name':each.branch_name,
                                        'bank_id':each.bank_account.id,
                                        'state':each.state,
                                        'operation_id':self.id,
                                        'amount':each.amount,
                                        'checks_id':each.id,
                                        'currency_code':each.payment_form.currency_id.id if(each.payment_form) else each.currency_id.id,})]        
        self.checks_paid_ids = check_list       

    
    def search_issue_check_data(self):
   
        domain = [('check_type', '=', 'outbound')]
        check_list = []
        if self.checks_paid_ids:
            self.checks_paid_ids = None
        if self.check_number:
            domain += [('name', 'ilike', '%'+self.check_number+'%')]
        if self.acc_number:
            domain += [('customer_bank_acc', 'ilike', '%'+self.acc_number+'%')]
        

        if self.due_date:
            domain += [('due_date', '=', self.due_date)]
        if self.bank_id:
            domain += [('bank_account', '=', self.bank_id.id)]
        if self.amount:
            domain += [('amount', '=', self.amount)]
        if self.issuer_id:
            domain += [('issuer_names', '=', self.issuer_id.id)]
        if self.transfered_bank:
            domain += [('transfer_bank','=',self.transfered_bank.id)]
        if self.received_date:
            domain += [('received_date', '=', self.received_date)]
        if domain:
            check_ids = self.env['checks.paid'].search(domain)
            for each in check_ids:
                check_list += [(0, 0, {'check_name':each.name,
                                        'acc_number':each.customer_bank_acc,
                                        'due_date':each.due_date,
                                        'received_date':each.received_date,

                                        'issuer_names':each.issuer_names.id,
                                        #'transfer_bank': each.transfer_bank.id,

                                        'branch_name':each.branch_name,
                                        'bank_id':each.bank_account.id,
                                        'state':each.state,
                                        'operation_id':self.id,
                                        'amount':each.amount,
                                        'checks_id':each.id,
                                        'currency_code':each.payment_form.currency_id.id if(each.payment_form) else each.currency_id.id,})]
        self.checks_paid_ids = check_list
    
    def rejects_check(self):
        
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))


                
        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                #check_id = self.env['checks.paid'].search([('name', '=', each.check_name)] ,limit=1) #ensure one
                if(not each.checks_id.state in('success','transfer_to_vendor','transferred','issue') ):
                    raise UserError(_('Check with number (%s) can not be rejected'%(each.checks_id.name,)))
                #each.checks_id.reject_check()
                 #get account of differed checks with the same currency 
                
               
                payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id #USD, ILS , ....
                payment_currency_id = payment_currency.id
                payment_currency_name = payment_currency.name
                #make sure it's not default one 
                default_currency = self.env.user.company_id.currency_id.id 

                rejected_date= self.date_transaction
                if(each.checks_id.state == 'issue'):
                    if each.checks_id.payment_form:
                        debit = each.checks_id.payment_form.journal_id.default_debit_account_id #self.env['account.journal'].search([('bank_account_id', '=', self.withdraw_user_account[0].id)], limit=1).default_debit_account_id
                    elif each.checks_id.deposited_journal:
                        debit = each.checks_id.deposited_journal.default_debit_account_id
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
                if(each.checks_id.state == 'success'):
                    undercollection = self.env['account.journal'].search([('bank_account_id','=',each.checks_id.deposit_usr_account[0].id)], limit=1)
                    account_val = 1
                elif(each.checks_id.state == 'transfer_to_vendor'):
                    undercollection = self.env['account.account'].search([('code','=','111100')], limit=1) #account payable 
                    account_val = 0
                elif(each.checks_id.state == 'transferred'):
                    if each.checks_id.transfer_user_bank:
                        undercollection = self.env['account.journal'].search([('bank_account_id','=',each.checks_id.transfer_user_bank[0].id)], limit=1)
                    else:
                        undercollection = each.checks_id.transfer_bank
                    account_val = 1
                elif(each.checks_id.state == 'issue'):
                    undercollection = self.env['account.account'].search([('code','=','111100')], limit=1) #account payable
                    account_val = 0
                else:
                    raise UserError('Can not reject this type of checks')
                
                db_account_val = 1
                account_id_cr = undercollection
                account_id_db = debit
                if(not account_id_db):
                    raise UserError('There is no debit account with this user bank account')
                
                
                move_id = each.checks_id.create_journal_entry(rejected_date, account_id_cr, account_id_db, account_val, db_account_val)
                checks_log_obj = self.env['receive.check.log']
                if(each.checks_id.state != 'issue'):
                    each.checks_id.check_type = 'inbound'
                each.checks_id.state = 'rejected'
                each.checks_id.store_check_state(move_id)
                rec = {'state':'returned' if(each.checks_id.state == 'issue') else 'rejected', 'transaction':'Returned' if(each.checks_id.state == 'issue') else 'Rejected','date':rejected_date ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                checks_log_obj.create(rec)
                
              
                each.state = 'rejected'
                each.checks_id.state = 'rejected'
                each.checks_id.reject_date = self.date_transaction


    
    def cancel_bank_transfer(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if each.state not in ('transferred'):
                    raise UserError(_('Check  the CheckState plz should be Transferred'))
                else :
                    payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id #USD, ILS , ....
                    payment_currency_id = payment_currency.id
                    payment_currency_name = payment_currency.name
                    default_currency = self.env.user.company_id.currency_id.id 
                    cridit_account = each.checks_id.transfer_user_bank.journal_id
                    if(not payment_currency_id or default_currency == payment_currency_id):
                        debit_account = self.env.ref('deferred_checks.check_box_erpsmart')
                   
                    elif(payment_currency_id and payment_currency != default_currency):
                        code = "CB"
                        debit_account=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                       
                   
                    account_val = 1
                    db_account_val = 1
                    each.checks_id.deposit_date = self.date_transaction
                    move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit_account, debit_account,account_val,db_account_val)
                    each.state  = 'received'
                    each.checks_id.is_selected_check=False	
                    each.checks_id.state = 'received'
                    each.checks_id.store_check_state(move_id)
                    checks_log_obj = self.env['receive.check.log']
                    rec = {'state':'received', 'transaction':'cancel from ' + each.checks_id.transfer_bank.name,'date':self.date_transaction ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                    checks_log_obj.create(rec)




                

        
    
    def cancel_vendor_transfer(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if each.state not in ('transfer_to_vendor') :
                    raise UserError(_('Check  the CheckState plz should be transfer_to_vendor'))
                
                else  :
                    if each.checks_id.vendor_id.customer:
                        raise UserError(_("you can't cancel transfer to customer"))
                    else :
                        
                        payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id #USD, ILS , ....
                        payment_currency_id = payment_currency.id
                        payment_currency_name = payment_currency.name
                        default_currency = self.env.user.company_id.currency_id.id 
                        cridit_account =self.env['account.account'].search([('code', '=', '111100')],limit=1)
                  
                        if(not payment_currency_id or default_currency == payment_currency_id):
                            debit_account = self.env.ref('deferred_checks.check_box_erpsmart')
                    
                        elif(payment_currency_id and payment_currency != default_currency):
                            code = "CB"
                            debit_account=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                        
                    
                        account_val = 0
                        db_account_val = 1
                        each.checks_id.deposit_date = self.date_transaction
                        move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit_account, debit_account,account_val,db_account_val)
                        each.state  = 'received'
                        each.checks_id.state = 'received'
                        each.checks_id.is_selected_check=False	

                        each.checks_id.store_check_state(move_id)
                        checks_log_obj = self.env['receive.check.log']
                
                        rec = {'state':'received', 'transaction':'cancel from ' +each.checks_id.vendor_id.name,'date':self.date_transaction ,'creation_date':fields.Date.today(),'check_paid_id':each.checks_id.id}
                        checks_log_obj.create(rec)







                

        
    
    
    def transfer_to_bank(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        if self.selected_checks_detail_ids:
            journal = self.env['account.journal'].search([('name', '=', 'Checks')])
            line = []
            for each in self.selected_checks_detail_ids:
                line.append((0, 0, {
                            'type': 'src',
                            'name': ' Checks in collection',
                            'partner_id':each.issuer_names.id,
                            'price': each.amount,
                            'debit': each.amount,
                            'account_id': 1,
                            'date_maturity': each.due_date,
                            }))
                line.append((0, 0, {
                    'type': 'src',
                    'name': 'Check Box',
                    'partner_id':each.issuer_names.id,
                    'price': each.amount,
                    'credit': each.amount,
                    'account_id': self.env['account.account'].search([('name', '=', 'Check box')]).id,
                    'date_maturity': each.due_date,
                }))
                each.write({'operation_id':False})
            move_vals = {
    #             'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': datetime.today().date(),
            }
            move = self.env['account.move'].create(move_vals)
            return {'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': move.id,
                }
    
    # 
    # def deposit_to_account(self):
    #     if self.selected_checks_detail_ids:
    #         journal = self.env['account.journal'].search([('name','=','Checks')])
    #         line=[]
    #         for each in self.selected_checks_detail_ids:
    #             line.append((0,0,{
    #                         'type': 'src',
    #                         'name': ' current bank cash account ',
    #                         'partner_id':each.issuer_names.id,
    #                         'price': each.amount,
    #                         'debit': each.amount,
    #                         'account_id': 1,
    #                         'date_maturity': each.due_date,
    #                         }))
    #             line.append((0,0,{
    #                 'type': 'src',
    #                 'name': 'Checks in collection',
    #                 'partner_id':each.issuer_names.id,
    #                 'price': each.amount,
    #                 'credit': each.amount,
    #                 'account_id': 2,
    #                 'date_maturity': each.due_date,
    #             }))
    #             each.write({'operation_id':False})
    #         move_vals = {
    # #             'ref': inv.reference,
    #             'line_ids': line,
    #             'journal_id': journal.id,
    #             'date': datetime.today().date(),
    #         }
    #         move = self.env['account.move'].create(move_vals)
    #         return {'type': 'ir.actions.act_window',
    #             'res_model': 'account.move',
    #             'view_mode': 'form',
    #             'res_id': move.id,
    #             }
    '''
    
    def redeposit(self):
        if self.selected_checks_detail_ids:
            journal = self.env['account.journal'].search([('name', '=', 'Checks'),])
            journal = journal[0]
            line = []
            for each in self.selected_checks_detail_ids:
                #get check currency 
                undercollection = self.env.ref('deferred_checks.differed_check_erpsmart') # deb
                rejectedcheck = self.env.ref('deferred_checks.rejected_check_erpsmart') # cridit
                frompayment = each.checks_id.payment_form
                #get by currency 
                default_currency = self.env.user.company_id.currency_id
                if(frompayment): # from payment 
                    payment_currency = frompayment.currency_id
                    payment_currency_id = payment_currency.id
                    payment_currency_name = payment_currency.name
                    if(payment_currency_id and payment_currency != default_currency):
                        #try to catch undercollection account and diposit check with this currency 
                        code = "UC"
                        #must be reviewed
                        undercollection=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                        if(not undercollection):
                            raise UserError('While trying to deposit check (%s) can not find under collection checks account with %s currency'%(each.checks_id.name,payment_currency_name,))
                        code = "RC"
                        rejectedcheck=self.env['account.account'].search([('code','like',code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                        if(not rejectedcheck):
                            raise UserError('While trying to deposit check (%s) can not find rejected checks account with %s currency'%(each.checks_id.name,payment_currency_name,))    
                #total=self.currency_id.with_context(date=self.payment_date).compute(self.amount,self.company_id.currency_id)
                #if not each.checks_id.deposit_accnt:
                #    raise UserError(_('Enter Account Number For Deposit Check'))
                now = datetime.now()
                each.checks_id.deposit_date = now.strftime("%Y-%m-%d")
                
                account_val = 0
                db_account_val = 1
                account_id_db = undercollection
                account_id_cr = rejectedcheck
                move = each.checks_id.create_journal_entry(each.checks_id.deposit_date, account_id_cr, account_id_db, account_val, db_account_val)
                each.state = 'success'
                each.checks_id.state = 'success'
                flag = 0
                updated_amount = 0
                for each2 in each.checks_id.payment_form.checks_paid:
                    if each2.state != 'success' and each2.state != 'returned':
                        flag = 0
                        break
                    else:
                        if each2.state == 'success':
                            updated_amount = updated_amount + each2.amount
                        flag = 1
                if flag == 1:
                    each.checks_id.payment_form.write({'amount': updated_amount,
                                            'state': 'posted'})
                checks_log_obj = self.env['receive.check.log']
                rec = {'state':'success', 'transaction':'Success Fully ReDeposited to Account :-' + account_id_db.name, 'date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                checks_log_obj.create(rec)
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': move.id,
                }
    '''

    
    def draw_cash(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if not each.checks_id.state in ('received'):
                    raise UserError(_('Check with number (%s) can not be draw cash'%(each.checks_id.name,)))
                payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id  #USD, ILS , ....
                payment_currency_id = payment_currency.id
                payment_currency_name = payment_currency.name
                default_currency = self.env.user.company_id.currency_id.id
                expected_code = "CB"
                if payment_currency_id == default_currency:
                    cridit_account = self.env.ref('deferred_checks.check_box_erpsmart')

                else:
                    cridit_account = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if(not cridit_account):
                    raise UserError('You do not have checkbox account with %s currency'%(payment_currency_name,))      
                cridit = cridit_account
                expected_code = "cash"
                if payment_currency_id == default_currency:
                    debit_account = self.env['account.account'].search([('code','like',expected_code+"%"),'|', ('currency_id','=',payment_currency_id),('currency_id','=',False)], limit=1)
                else:
                    debit_account = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                if (not debit_account):
                    raise UserError('You do not have cash account with %s currency'%(payment_currency_name,))     
                debit = debit_account
                account_val = 0
                db_account_val = 1

                each.checks_id.deposit_date = self.date_transaction
                move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit, debit,account_val,db_account_val)
                each.state = 'drawcash'
                each.checks_id.state = 'drawcash'
                each.checks_id.store_check_state(move_id)
                checks_log_obj = self.env['receive.check.log']
                rec = {'state':'drawcash', 'transaction':'Draw Cash', 'date':self.date_transaction ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                checks_log_obj.create(rec)
        return True

        
    
    def recollect_check(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if not each.checks_id.state in ('backtoorigin'):
                    raise UserError(_('Check with number (%s) can not be recollect'%(each.checks_id.name,)))

                payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id  #USD, ILS , ....
                payment_currency_name = payment_currency.name
                default_currency = self.env.user.company_id.currency_id.id
                payment_currency_id = payment_currency.id or default_currency

                cridit_account = self.env['account.account'].search([('code', '=', '101200')],limit=1)#self.env['account.journal'].search([('bank_account_id','=',self.deposit_usr_account[0].id)], limit=1)
                if(not cridit_account):
                    raise UserError('You do not have receive checks account with %s currency'%(payment_currency_name,))      
                cridit = cridit_account
                expected_code = "CB"
                if not payment_currency_id or payment_currency_id == default_currency:
                    debit_account =  self.env.ref('deferred_checks.check_box_erpsmart')
                else:
                    debit_account = self.env['account.account'].search([('code','like',expected_code+"%"),('currency_id','=',payment_currency_id)], limit=1)
                if (not debit_account):
                    raise UserError('You do not have checkbox account with %s currency'%(payment_currency_name,))     
                debit = debit_account
                account_val = 0
                db_account_val = 1

                each.checks_id.deposit_date =  self.date_transaction
                move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit, debit,account_val,db_account_val)
                each.state = 'received'
                each.checks_id.state = 'received'
                each.checks_id.is_selected_check=False

                each.checks_id.store_check_state(move_id)
                each.check_type = 'inbound'
                each.checks_id.check_type = 'inbound'
                checks_log_obj = self.env['receive.check.log']
                rec = {'state':'received', 'transaction':'Received', 'date':self.date_transaction ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                checks_log_obj.create(rec)
        return True
    
    def validate_request(self):
        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if each.checks_id.state == 'transferred':
                    view = self.env.ref('deferred_checks.check_operation_transfer_back_wizard_form_view')
                    return {
                        'name':_("Select Reason"),#Name You want to display on wizard
                        'view_mode': 'form',
                        'view_id': view.id,
                        'view_type': 'form',
                        'res_model': 'check.operation.transfer.backtoorigin.wizard',# With . Example sale.order
                        'type': 'ir.actions.act_window',
                        'target': 'new'
                    }
            
            self.back_to_origin() 
    
    def back_to_origin(self):
        now = datetime.now()
        if self.date_transaction > now.strftime("%Y-%m-%d"):
            raise UserError(_('The Transaction Date Should Be Before Current Date'))

        
        if self.selected_checks_detail_ids:
            for each in self.selected_checks_detail_ids:
                if not each.checks_id.state in ('success','transferred','rejected','received','transfer_to_vendor'):
                    raise UserError(_('Check with number (%s) can not be back to origin'%(each.checks_id.name,)))
                if(each.checks_id.state not in ('rejected', 'received') ):
                    # state not in ('rejected', 'recieved')
                    each.checks_id.reject_check() #reject check
                payment_currency = each.checks_id.payment_form.currency_id if each.checks_id.payment_form else each.checks_id.currency_id #USD, ILS , ....
                payment_currency_id = payment_currency.id
                payment_currency_name = payment_currency.name
                default_currency = self.env.user.company_id.currency_id.id 
                #if(not self.state == 'success'):
                #    raise UserError(_('Check with number (%s) have not be deposted'%(self.name,)))
                if (each.checks_id.state == 'rejected'):
                    if(not payment_currency_id or default_currency == payment_currency_id):
                        #undercollection = self.env.ref('deferred_checks.differed_check_erpsmart')
                        rejectedcheck = self.env.ref('deferred_checks.rejected_check_erpsmart')
                    else:
                        expected_code = "RC"
                        if default_currency == payment_currency_id:
                            rejectedcheck = self.env['account.account'].search([('code','like',expected_code+"%"),'|', ('currency_id','=',payment_currency_id),('currency_id','=',False)], limit=1)    
                        else:
                            rejectedcheck = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1) 
                        if(not rejectedcheck):
                            raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))     
                    #from rejected check to account receivable 
                    cridit = rejectedcheck #rejected check
                    debit = self.env['account.account'].search([('code', '=', '101200')],limit=1)

                    
                    each.checks_id.deposit_date =  self.date_transaction
                    
                    account_val = 0
                    db_account_val = 1
                    move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit, debit,account_val,db_account_val)
                    each.state = 'backtoorigin'
                    each.checks_id.state = 'backtoorigin'
                    each.checks_id.store_check_state(move_id)
                    checks_log_obj = self.env['receive.check.log']
                    rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN','date':self.date_transaction ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                    checks_log_obj.create(rec) 
                    
                    debit = self.env['account.account'].search([('code', '=', '101200')],limit=1) #each.payment_form.
                    expected_code = "RCF"
                    cridit_account = self.env['account.account'].search([('code','like',expected_code+"%")], limit=1) 
                    #print " cridit_account is",cridit_account.name
                    if(not cridit_account):
                        raise UserError("You do not have rejected checks fee's account with %s currency"%(payment_currency_name,))     
                  

                    each.checks_id.deposit_date= self.date_transaction
                    each.checks_id.is_checks_fees=True
                    
                    move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit_account, debit,account_val,db_account_val)
                    each.state = 'backtoorigin'
                    each.checks_id.state = 'backtoorigin'
                    each.checks_id.store_check_state(move_id)
                    each.checks_id.is_checks_fees=False
                    checks_log_obj = self.env['receive.check.log']
                    #rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN', 'date':fields.Date.today(), 'check_paid_id':each.id}
                    #checks_log_obj.create(rec)
                    

                elif (each.checks_id.state == 'received'):
                    if(not payment_currency_id or default_currency == payment_currency_id):
                        #undercollection = self.env.ref('deferred_checks.differed_check_erpsmart')
                        recievedcheck = self.env.ref('deferred_checks.check_box_erpsmart')
                    else:
                        expected_code = "CB"
                        recievedcheck = self.env['account.account'].search([('code','like',expected_code+"%"), ('currency_id','=',payment_currency_id)], limit=1)
                        if(not recievedcheck):
                            raise UserError('You do not have rejected checks account with %s currency'%(payment_currency_name,))     
                    #from rejected check to account receivable 
                    cridit = recievedcheck
                    customer = self.env['account.account'].search([('code', '=', '101200')],limit=1)
                    debit = self.env['account.account'].search([('code', '=', '101200')],limit=1) #each.checks_id.payment_form.partner_id
                    #now = datetime.now()

                    each.checks_id.deposit_date =  self.date_transaction
                    
                    account_val = 0
                    db_account_val = 1
                    move_id = each.checks_id.create_journal_entry(each.checks_id.deposit_date, cridit, debit,account_val,db_account_val)
                    each.state = 'backtoorigin'
                    each.checks_id.state = 'backtoorigin'
                    each.checks_id.store_check_state(move_id)
                    checks_log_obj = self.env['receive.check.log']
                    rec = {'state':'backtoorigin', 'transaction':'Back To ORIGIN', 'date':self.date_transaction ,'creation_date':fields.Date.today(), 'check_paid_id':each.checks_id.id}
                    checks_log_obj.create(rec)
        return True


class CheckDetails(models.Model):
    _name = 'check.operation.details'

    check_name = fields.Char(string='Check Number')
    issuer_names = fields.Many2one('res.partner', string='Issuer Name')
    issuer_display_names =fields.Char(string='Issuer Name')
    branch_name = fields.Char(string='Branch Name')

    bank_id = fields.Many2one('res.bank', string='Bank')
    due_date = fields.Date(string='Due Date')
    amount = fields.Float(string='Amount')
    acc_number = fields.Char(string='Account Number',compute="set_acc_number")
    state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('drawcash','Draw Cash'),
                              ('issue', 'Issued Deferred'),
                              ('transfer_to_vendor', 'Transfared To Vendor')], string='State', default='received')


    operation_id = fields.Many2one('check.operation', string="Operation")
    checks_id = fields.Many2one('checks.paid', string="Check Paid ID")
    selected_check = fields.Boolean(string='Select')
    select_all = fields.Boolean(string='Select all')
    currency_code = fields.Many2one('res.currency','Currency')
    received_date= fields.Date('Received Date')
    def set_acc_number(self):
        for each in self:
            each.acc_number = each.checks_id.customer_bank_acc
            each.received_date = each.checks_id.received_date
            each.due_date = each.checks_id.due_date


#     
#     def add_to_selected_list(self):
#         self.operation_id.write({'selected_checks_detail_ids':[(0, 0, {'check_name':self.check_name,
#                                     'due_date':self.due_date,
#                                     'issuer_names':self.issuer_names.id,
#                                     'branch_name':self.branch_name,
#                                     'bank_id':self.bank_id.id,
#                                     'state':self.state,
#                                     'operation_id':self.operation_id.id,
#                                     'amount':self.amount,
#                                     'check_op_id':self.id,
#                                     'checks_id':self.checks_id.id})]})
#         vals = {
#             'type': 'ir.actions.client',
#             'tag': 'reload',
#         }
# #         self.write({'operation_id':False})
#         self.unlink()
#         return vals

class SelectedCheckDetails(models.Model):
    _name = 'selected.check.operation.details'
    acc_number = fields.Char(string='Account Number')

    check_name = fields.Char(string='Check Number')
    issuer_names = fields.Many2one('res.partner', string='Issuer Name')
    issuer_display_names = fields.Char(string='Issuer Name')
    branch_name = fields.Char(string='Branch Name')
    bank_id = fields.Many2one('res.bank', string='Bank')
    due_date = fields.Date(string='Due Date')
    received_date= fields.Date('Received Date')
    
    amount = fields.Float(string='Amount')
    state = fields.Selection([('received', 'Received'),
                              ('withdraw_from_bank', 'Withdraw from bank'),
                              ('transferred', 'Transferred'),
                              ('success', 'Success'),
                              ('rejected', 'Rejected'),
                              ('returned', 'Returned'),
                              ('backtoorigin', 'BACK TO ORIGIN'),
                              ('drawcash','Draw Cash'),
                              ('issue', 'Issued Deferred'),
                              ('transfer_to_vendor', 'Transfared To Vendor')], string='State', default='received')

    check_op_id = fields.Many2one('check.operation.details', string='Check Op id')
    operation_id = fields.Many2one('check.operation', string="Operation")
    checks_id = fields.Many2one('checks.paid', string="Check Paid ID")
    currency_code = fields.Many2one('res.currency','Currency')
    
    def delete_selected_list(self):
        #operation_details_id = self.env['check.operation.details'].search([('check_name', '=', self.check_name)])
        #operation_details_id.write({'operation_id':self.operation_id.id})
        currency_id = self.currency_code if self.currency_code else (self.checks_id.payment_form.currency_id if self.checks_id.payment_form else self.checks_id.currency_id)
        if not currency_id: #Company
            currency_id = self.env.user.company_id.currency_id
        obj = {'check_name':self.check_name,
                'acc_number':self.acc_number,
                'due_date':self.due_date,
                'received_date':self.received_date,

                'issuer_names':self.issuer_names.id,
                'issuer_display_names':self.issuer_display_names,
                'branch_name':self.branch_name,
                'bank_id':self.bank_id.id,
                'state':self.state,
                'operation_id':self.operation_id.id,
                'amount':self.amount,
                'currency': currency_id.id,
                'check_op_id':self.id}
        operation = self.operation_id
        operation.write({'checks_paid_ids':[(0, 6, obj)]})
        operation.number_check -= 1
        operation.total_amount -= self.amount * currency_id.rate
        self.unlink()

        vals = {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
        
        return vals
