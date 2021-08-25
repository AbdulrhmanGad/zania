# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.addons.base.models.qweb import QWeb


class IrQWeb(models.AbstractModel, QWeb):
    _inherit = 'ir.qweb'

    @api.model
    def _render(self, id_or_xml_id, values=None, **options):
        values = values or {}
        context = dict(self.env.context, **options)
        if 'lang_direction' in values:
            return super(IrQWeb, self)._render(id_or_xml_id, values=values, **options)
        Language = self.env['res.lang']
        lang = context.get('lang', 'en_US')
        directions = Language.get_languages_dir()
        direction = directions.get(lang, 'ltr')
        values['lang_direction'] = direction
        return super(IrQWeb, self)._render(id_or_xml_id, values=values, **options)

