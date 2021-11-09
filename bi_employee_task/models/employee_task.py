# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class hr_employee(models.Model):
    _inherit = 'hr.employee'


    task_count = fields.Integer(compute='compute_tasks_count', string='Task Count',readonly=True)


    @api.depends('user_id')
    def compute_tasks_count(self):
        usr_id = 0
        for employee in self:
            if employee.user_id:
                usr_id = employee.user_id.id
                task_ids = self.env['project.task'].search([('user_id','=',usr_id)])
                employee.task_count = len(task_ids)
            else:
                employee.task_count = 0


        return{
            'name':'Employee Task',
            'res_model':'project.task',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'list,form,kanban,calendar,pivot,graph',
            'context':{'group_by':'stage_id'},
            'domain': [('user_id', '=', usr_id)],
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
