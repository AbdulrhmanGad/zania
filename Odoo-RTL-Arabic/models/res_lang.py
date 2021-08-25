# -*- coding: utf-8 -*-

from odoo import models, api
import odoo


class Language(models.Model):
    _inherit = 'res.lang'


    @odoo.tools.ormcache(skiparg=1)
    def _get_languages_dir(self):
        langs = self.search([('active', '=', True)])
        return dict([(lg.code, lg.direction) for lg in langs])


    def get_languages_dir(self):
        return self._get_languages_dir()


    def write(self, vals):
        self._get_languages_dir.clear_cache(self)
        return super(Language, self).write(vals)