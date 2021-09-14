# -*-coding:utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class CheckTransferWizard(models.TransientModel):
    _name = 'check.operation.transfer.wizard'

    transfer_account = fields.Many2one('res.bank', string='Transfer To Bank', required=True)
    trans_user_account = fields.Many2one('res.partner.bank','Transfet To Account',domain=lambda self:[('id', 'in',self.get_valid_ids())])


     
    def get_valid_ids(self):
        self.env.cr.execute('Select p_bank.id from res_partner_bank as p_bank join res_bank as bank on bank.id = p_bank.bank_id \
                                join account_journal as journal on journal.bank_account_id = p_bank.id \
                                where p_bank.company_id=%s and bank.active=True', 
                                (self.env.user.company_id[0].id,))
        data = self.env.cr.dictfetchall()
        return [b['id'] for b in data]


    @api.onchange('trans_user_account')
    def _set_bank_branch(self):
        if self.trans_user_account:
            return {'value':{'transfer_account':self.trans_user_account.bank_id[0].id}}

    
    def transfer_check(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        
        for record in  operation_id.selected_checks_detail_ids:
            if record.checks_id.check_type == 'inbound':
                if record.checks_id.state in ('received',):
                    record.checks_id.transfer_bank = self.transfer_account
                    record.checks_id.transfer_user_bank = self.trans_user_account
                    record.checks_id.transfer_check()
                    record.state = record.checks_id.state
                
                else:
                    raise UserError(_("Check (%s) can not be transfered"%(record.checks_id.name,)))
            else:
                raise UserError(_("These are Issued Checks. Please check (%s)"%(record.checks_id.name,)))
        return {'type': 'ir.actions.act_window_close'}
        

    @api.model
    def create (self, vals):
        res = super(CheckTransferWizard, self).create(vals)
        operation_id = self.env['check.operation'].browse(self._context.get('active_id'))
        operation_id.transfer_bank = self.env['res.bank'].search([('id', '=', vals.get('transfer_account'))]).name
        return res


class CheckTransferBackWizard(models.TransientModel):
    _name = 'check.operation.transfer.backtoorigin.wizard'

    origin_type = fields.Selection((('r','Rejected Checks'), ('ur','User Request')),'Select Reason')

    
    def back_to_origin(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        for record in  operation_id.selected_checks_detail_ids:
            if record.checks_id.check_type == 'inbound':
                if record.checks_id.state in ('transferred',) and self.origin_type == 'ur':
                    record.checks_id.back_to_origin(False)
                    #get select type
                else:
                    #select type = back to origin (2nd select)
                    record.checks_id.back_to_origin()
                record.state = 'backtoorigin'
            else:
                raise UserError(_("These are Issued Checks."))
            
        return {'type': 'ir.actions.act_window_close'}
        
    @api.model
    def create (self, vals):
        res = super(CheckTransferBackWizard, self).create(vals)
        operation_id = self.env['check.operation'].browse(self._context.get('active_id'))
        #operation_id.transfer_bank = self.env['res.bank'].search([('id', '=', vals.get('transfer_account'))]).name
        return res


class CheckwithdrawWizard(models.TransientModel):
    _name = 'check.operation.withdraw.wizard'

    withdraw_account = fields.Many2one('res.bank', string='Withdraw From Bank', required=True)
    withdraw_user_account = fields.Many2one('res.partner.bank','Withdraw To Account',domain=lambda self:[('id', 'in',self.get_valid_ids())])


     
    def get_valid_ids(self):
        self.env.cr.execute('Select p_bank.id from res_partner_bank as p_bank join res_bank as bank on bank.id = p_bank.bank_id \
                                join account_journal as journal on journal.bank_account_id = p_bank.id \
                                where p_bank.company_id=%s and bank.active=True', 
                                (self.env.user.company_id[0].id,))
        data = self.env.cr.dictfetchall()
        return [b['id'] for b in data]


    @api.onchange('withdraw_user_account')
    def _set_bank_branch(self):
        if self.withdraw_user_account:
            return {'value':{'withdraw_account':self.withdraw_user_account.bank_id[0].id}}


    
    def withdraw_check(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        for record in  operation_id.selected_checks_detail_ids:
            if record.checks_id.check_type == 'outbound':
                    record.checks_id.transfer_bank = self.withdraw_account
                    record.checks_id.withdraw_user_account = self.withdraw_user_account
                    record.checks_id.withdraw_check()
                    record.state = record.checks_id.state
            else:
                raise UserError(_("These are Receive Checks."))
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create (self, vals):
        res = super(CheckwithdrawWizard, self).create(vals)
        operation_id = self.env['check.operation'].browse(self._context.get('active_id'))
        operation_id.transfer_bank = self.env['res.bank'].search([('id', '=', vals.get('withdraw_account'))]).name
        return res


class CheckDepositwizard(models.TransientModel):
    _name = 'check.operation.deposit.wizard'
    deposite_account = fields.Many2one('res.bank', string="Deposit Account", required=True)
    deposite_journal_id = fields.Many2one('account.journal', string='Deposit Account Journal', required=True,
                                      domain=[('type', 'in', ('cash', 'bank'))],
                                      default=lambda self: self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))], limit=1))
    deposite_bank_account = fields.Many2one('res.partner.bank','Deposit User Account',domain=lambda self:[('id', 'in',self.get_valid_ids())])


     
    def get_valid_ids(self):
        
        # join jornals on bank_account_id
        self.env.cr.execute('Select p_bank.id from res_partner_bank as p_bank join res_bank as bank on bank.id = p_bank.bank_id \
                                join account_journal as journal on journal.bank_account_id = p_bank.id \
                                where p_bank.company_id=%s and bank.active=True', 
                                (self.env.user.company_id[0].id,))
        data = self.env.cr.dictfetchall()
        return [b['id'] for b in data]

    @api.onchange('deposite_bank_account')
    def _set_bank_branch(self):
        if self.deposite_bank_account:
            return {'value':{'deposite_account':self.deposite_bank_account.bank_id[0].id}}


    
    def check_deposit(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        for record in  operation_id.selected_checks_detail_ids:

            if record.checks_id.check_type == 'inbound':
                if record.checks_id.state in ('success', 'rejected', 'returned'):
                    raise UserError(_("Selected checks cannot be deposit."))
                elif record.checks_id.state in ('received', 'transferred'):
                    record.checks_id.deposit_accnt = self.deposite_account
                    record.checks_id.deposit_usr_account = self.deposite_bank_account
                    record.checks_id.deposited_journal = self.deposite_journal_id
                    record.checks_id.deposit_check()
                    record.state = record.checks_id.state
                else:
                    raise UserError(_("can't deposit check (%s)"%(record.checks_id.name)))
            else:
                raise UserError(_("Issued check (%s)"%(record.checks_id.id)))
        return {'type': 'ir.actions.act_window_close'}


class CheckRedepositwizard(models.TransientModel):
    _name = 'check.operation.redeposit.wizard'
    deposite_account = fields.Many2one('res.bank', string="Deposit Account", required=True)
    deposite_journal_id = fields.Many2one('account.journal', string='Deposit Account Journal', required=True,
                                      domain=[('type', 'in', ('cash', 'bank'))],
                                      default=lambda self: self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))], limit=1))
    deposite_bank_account = fields.Many2one('res.partner.bank','Deposit User Account',domain=lambda self:[('id', 'in',self.get_valid_ids())])


     
    def get_valid_ids(self):
        # join jornals on bank_account_id
        self.env.cr.execute('Select p_bank.id from res_partner_bank as p_bank join res_bank as bank on bank.id = p_bank.bank_id \
                                join account_journal as journal on journal.bank_account_id = p_bank.id \
                                where p_bank.company_id=%s and bank.active=True', 
                                (self.env.user.company_id[0].id,))
        data = self.env.cr.dictfetchall()
        return [b['id'] for b in data]
        
    @api.onchange('deposite_bank_account')
    def _set_bank_branch(self):
        if self.deposite_bank_account:
            return {'value':{'deposite_account':self.deposite_bank_account.bank_id[0].id}}


    
    def check_redeposit(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        for record in  operation_id.selected_checks_detail_ids:

            if record.checks_id.check_type == 'inbound':
                if record.checks_id.state in ('success',):
                    raise UserError(_("Selected checks cannot be redeposit."))
                elif record.checks_id.state in ('rejected',):
                    record.checks_id.deposit_accnt = self.deposite_account
                    record.checks_id.deposit_usr_account = self.deposite_bank_account
                    record.checks_id.deposited_journal = self.deposite_journal_id
                    record.checks_id.redeposit_check()
                    record.state = record.checks_id.state
                else:
                    raise UserError(_("can't redeposit check (%s) ,Just rejected checks can be redeposit"%(record.checks_id.name)))    
            else:
                    raise UserError(_("These are Issued Checks."))
        return {'type': 'ir.actions.act_window_close'}


class CheckRejectwizard(models.TransientModel):
    _name = 'check.operation.reject.wizard'

    
    def check_reject(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False) or []
        ckoperation_obj = self.env['check.operation']
        operation_id = ckoperation_obj.search([('id', '=', active_id)])
        for record in  operation_id.selected_checks_detail_ids:
            # if record.checks_id.payment_form.payment_type == 'inbound':
            if record.checks_id.check_type == 'inbound':

                if record.checks_id.state in ('rejected', 'returned'):
                    raise UserError(_("Selected checks cannot be rejected."))
                elif record.checks_id.state in ('success','received', 'transferred'):
                    record.checks_id.deposit_accnt = self.deposite_account
                    record.checks_id.deposit_usr_account = self.deposite_bank_account
                    record.checks_id.deposited_journal = self.deposite_journal_id
                    record.checks_id.deposit_check()
                    record.state = record.checks_id.state
            else:
                    raise UserError(_("These are Issued Checks."))
        return {'type': 'ir.actions.act_window_close'}
