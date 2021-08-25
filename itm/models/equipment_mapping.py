# Copyright (C) 2021 TREVI Software
# Copyright (C) 2014 Leandro Ezequiel Baldi <baldileandro@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, fields, models


class ItEquipmentMapping(models.Model):
    _name = "itm.equipment.mapping"
    _description = "Network Share Mapping"

    equipment_id = fields.Many2one("itm.equipment", "Asset", ondelete="cascade")
    name = fields.Char("Share Name", required=True)
    path = fields.Char("Filesystem Path", required=True)
    line_ids = fields.One2many(
        "itm.equipment.mapping.line", "map_id", "Permission lines"
    )


class ItEquipmentMappingLine(models.Model):
    _name = "itm.equipment.mapping.line"
    _description = "Network Share Mapping Line"

    def _compute_name(self):
        for rec in self:
            _name = _("Unknown")
            if rec.adobj_id:
                _name = rec.adobj_id.name
            rec.name = _name

    map_id = fields.Many2one("itm.equipment.mapping", "Mapping")
    name = fields.Char(string="Name", compute="_compute_name", store=True)
    adobj_id = fields.Many2one(
        comodel_name="itm.service.ad.object", string="AD object name"
    )
    type = fields.Selection(
        [
            ("simple", _("Simple Sharing")),
            ("advanced", _("Advanced Sharing")),
        ]
    )
    perm_simple = fields.Selection(
        [
            ("read", _("Read")),
            ("write", _("Read/Write")),
        ],
        string="Simple permissions",
    )
    perm_advanced = fields.One2many(
        "itm.equipment.mapping.permission.advanced", "line_id", "Advanced permissions"
    )


class ItMappingAdvancedPermissions(models.Model):
    _name = "itm.equipment.mapping.permission.advanced"
    _description = "Advanced Share Mapping Permission"

    name = fields.Char()
    line_id = fields.Many2one("itm.equipment.mapping.line", "Share mapping")
