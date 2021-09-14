# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging
from io import BytesIO
from odoo import models
try:
    import xlsxwriter
except ImportError:
    _logger.debug("Can not import xlsxwriter`.")


class ReportXlsxAbstract(models.AbstractModel):
    _name = "report.deferred_checks.check_report_xls.xlsx"
    _description = "Abstract XLSX Report"

    def generate_xlsx_report(self, workbook, data, partners):

        print(">>>>>>>>>>", partners)
        print("XXX", data)
        print("EEEEE", workbook)
    def get_workbook_options(self):
        """
        See https://xlsxwriter.readthedocs.io/workbook.html constructor options
        :return: A dictionary of options
        """
        return {}
    def _get_objs_for_report(self, docids, data):
        """
        Returns objects for xlx report.  From WebUI these
        are either as docids taken from context.active_ids or
        in the case of wizard are in data.  Manual calls may rely
        on regular context, setting docids, or setting data.

        :param docids: list of integers, typically provided by
            qwebactionmanager for regular Models.
        :param data: dictionary of data, if present typically provided
            by qwebactionmanager for TransientModels.
        :param ids: list of integers, provided by overrides.
        :return: recordset of active model for ids.
        """
        if docids:
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])
        return self.env[self.env.context.get("active_model")].browse(ids)

    def create_xlsx_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data, self.get_workbook_options())
        self.generate_xlsx_report(workbook, data, objs)
        workbook.close()
        file_data.seek(0)
        return file_data.read(), "xlsx"

class StockReport(models.TransientModel):
    _name = "due.date.report"
    _description = "Check Report"

    due_date = fields.Date(string='Due Date', default=datetime.today(), required=1)
    check_type = fields.Selection([('inbound', 'Received Check'),
                                   ('outbound', 'Issued Check'),
                                   ], string='Type of Check', required=1)
    due_date_exceed = fields.Boolean(string='Duded Checks', default=False)
    daily_report = fields.Boolean(string='Daily Report', default=False)

    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'checks.paid'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            #WWWWWWWWWWWWWW
            return {
                'type': 'ir.actions.client',
                'report_name': 'deferred_checks.due_date_check_report_xls.xlsx',
                'datas': datas,
                'name': 'Check Report'
            }
