# -*- coding: utf-8 -*-
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import datetime
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object


class CheckDueDateReportXls(ReportXlsx):

    def get_total_amount(self, check_obj):
        total = 0
        for each in check_obj:
            total = total + each.amount
        return total

    def get_lines(self, data):
        lines = []
        if data['form']['due_date_exceed']:
            check_obj = self.env['checks.paid'].search([('check_type', '=', data['form']['check_type']),
                                                        ('due_date', '<=', datetime.datetime.today()),
                                                        ('state', '=', 'received')])
        elif data['form']['daily_report']:
            check_obj = self.env['checks.paid'].search([('check_type', '=', data['form']['check_type']),
                                                        ('received_date', '=', datetime.datetime.today().strftime('%Y-%m-%d')),
                                                        ])
        else:
            check_obj = self.env['checks.paid'].search([('check_type', '=', data['form']['check_type']),
                                                        ('due_date', '<', data['form']['due_date']),
                                                        ])
        total_amount = self.get_total_amount(check_obj)
        for obj in check_obj:
            vals = {
                'issuer_name': obj.issuer_names.name,
                'bank_account': obj.bank_account.name,
                'due_date': obj.due_date,
                'amount': obj.amount,
                'payment_ref': obj.payment_form.name,
                'state': obj.state,
            }
            lines.append(vals)
        return lines, total_amount

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range('A2:L2', 'Report Date: ' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M %p")), format1)
        if data['form']['due_date_exceed']:
            sheet.merge_range('A3:L3', 'Expired Checks', format11)
        else:
            sheet.merge_range('A3:L3', 'Checks Info', format11)
        total_amount = self.get_lines(data)[1]
        sheet.merge_range('A4:L4', 'Total AMount: ' + str(total_amount), format11)
        sheet.merge_range(4, 0, 4, 2, 'Issuer Name', format21)
        sheet.merge_range(4, 3, 4, 5, 'Bank Account', format21)
        sheet.merge_range(4, 6, 4, 7, 'Due Date', format21)
        sheet.write(4, 8, 'Amount', format21)
        sheet.merge_range(4, 9, 4, 11, 'Payment Ref', format21)
        prod_row = 5
        get_line = self.get_lines(data)
        for each in get_line[0]:
            sheet.merge_range(prod_row, 0, prod_row, 2, each['issuer_name'], font_size_8)
            sheet.merge_range(prod_row, 3, prod_row, 5, each['bank_account'], font_size_8)
            sheet.merge_range(prod_row, 6, prod_row, 7, each['due_date'], font_size_8)
            sheet.write(prod_row, 8, each['amount'], font_size_8)
            sheet.merge_range(prod_row, 9, prod_row, 11, each['payment_ref'], font_size_8)
            prod_row = prod_row + 1

# CheckDueDateReportXls('report.deferred_checks.due_date_check_report_xls.xlsx', 'checks.paid')
CheckDueDateReportXls()
