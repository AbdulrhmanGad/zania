# -*- coding: utf-8 -*-
import datetime
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object


class CheckReportXls(ReportXlsx):

    def get_lines(self, data):
        lines = []
        check_obj = self.env['checks.paid'].search([('check_type', '=', data['form']['check_type']),
                                                    ('received_date', '>=', data['form']['date_from']),
                                                    ('received_date', '<=', data['form']['date_to'])])
        if data['form']['state']:
            check_obj = self.env['checks.paid'].search([('check_type', '=', data['form']['check_type']),
                                                        ('received_date', '>=', data['form']['date_from']),
                                                        ('received_date', '<=', data['form']['date_to']),
                                                        ('state', '=', data['form']['state'])])
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
        return lines

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
        sheet.merge_range('A3:L3', 'Report Date: ' + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M %p")), format1)
        if data['form']['check_type'] == 'received_check':
            sheet.merge_range('A4:L4', 'Received Checks', format11)
        if data['form']['check_type'] == 'issued_check':
            sheet.merge_range('A4:L4', 'Issued Checks', format11)
        if data['form']['check_type'] == 'transferred_check':
            sheet.merge_range('A4:L4', 'Transferred Checks', format11)
        sheet.merge_range(4, 0, 4, 2, 'Issuer Name', format21)
        sheet.merge_range(4, 3, 4, 5, 'Bank Account', format21)
        sheet.merge_range(4, 6, 4, 7, 'Due Date', format21)
        sheet.write(4, 8, 'Amount', format21)
        sheet.merge_range(4, 9, 4, 11, 'Payment Ref', format21)
        prod_row = 5
        get_line = self.get_lines(data)
        for each in get_line:
            sheet.merge_range(prod_row, 0, prod_row, 2, each['issuer_name'], font_size_8)
            sheet.merge_range(prod_row, 3, prod_row, 5, each['bank_account'], font_size_8)
            sheet.merge_range(prod_row, 6, prod_row, 7, each['due_date'], font_size_8)
            sheet.write(prod_row, 8, each['amount'], font_size_8)
            sheet.merge_range(prod_row, 9, prod_row, 11, each['payment_ref'], font_size_8)
            prod_row = prod_row + 1

CheckReportXls()
# CheckReportXls('report.deferred_checks.check_report_xls.xlsx', 'checks.paid')
