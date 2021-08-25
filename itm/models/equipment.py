##############################################################################
#
#    Copyright (C) 2014 Leandro Ezequiel Baldi
#    <baldileandro@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import base64

from odoo import _, api, fields, models
from odoo.modules.module import get_module_resource


class ItEquipmentBrand(models.Model):
    _name = "itm.equipment.brand"
    _description = "IT Asset Brand Name"

    name = fields.Char(required=True)
    is_computer = fields.Boolean("Computing Devices")
    is_network = fields.Boolean("Network Devices")
    is_accessories = fields.Boolean("Computing Accessories")


class ItEquipment(models.Model):
    _name = "itm.equipment"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _description = "IT Asset"

    @api.depends("virtual_ids")
    def _compute_virtual_count(self):
        for equipment in self:
            equipment.virtual_count = len(equipment.virtual_ids)

    @api.depends("access_ids")
    def _compute_access_count(self):
        for equipment in self:
            equipment.access_count = len(equipment.access_ids)

    @api.depends("backup_ids")
    def _compute_backup_count(self):
        for equipment in self:
            equipment.backup_count = len(equipment.backup_ids)

    @api.model
    def _get_default_image(self):
        image_path = get_module_resource(
            "itm", "static/src/img", "default_image_equipment.png"
        )
        return base64.b64encode(open(image_path, "rb").read())

    @api.model
    def _get_partner_id(self):
        # Get the partner from either asset or site
        #
        if self.env.context.get("active_model") == "itm.equipment":
            equip = self.env["itm.equipment"].browse(self.env.context.get("active_id"))
            if equip.partner_id:
                return equip.partner_id.id
        elif self.env.context.get("active_model") == "itm.site":
            site = self.env["itm.site"].browse(self.env.context.get("active_id"))
            if site.partner_id:
                return site.partner_id.id
        return False

    @api.model
    def _get_site_id(self):
        if self.env.context.get("active_model") == "itm.equipment":
            equip = self.env["itm.equipment"].browse(self.env.context.get("active_id"))
            if equip.site_id:
                return equip.site_id.id
        return False

    # For openerp structure
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
    )
    site_id = fields.Many2one(
        "itm.site", "Site", required=True, tracking=True, default=_get_site_id
    )
    active = fields.Boolean(default=True, tracking=True)
    # Counts
    access_count = fields.Integer(
        compute="_compute_access_count", string="Credentials Count", store=False
    )
    access_ids = fields.One2many("itm.access", "equipment_id", string="Credentials")
    backup_count = fields.Integer(compute="_compute_backup_count")
    backup_ids = fields.One2many("itm.backup", "equipment_id", "Backups")
    virtual_count = fields.Integer(
        compute="_compute_virtual_count", string="Guests", store=False
    )
    virtual_ids = fields.One2many("itm.equipment", "virtual_parent_id", "Guest(s)")
    # General Info
    identification = fields.Char(
        compute="_compute_identification", string="Complete Name", store=True
    )
    name = fields.Char("Name", required=True, tracking=True)
    brand_id = fields.Many2one("itm.equipment.brand", "Brand")
    model = fields.Char()
    partner_id = fields.Many2one(
        "res.partner",
        "Partner",
        required=True,
        domain="[('manage_it','=',1)]",
        tracking=True,
        default=_get_partner_id,
    )
    function_ids = fields.Many2many(
        "itm.equipment.function",
        "equipment_function_rel",
        "equipment_id",
        "function_id",
        "Functions",
    )
    description = fields.Char("Description", required=False)
    image = fields.Binary(
        "Photo",
        default=_get_default_image,
        help="Equipment Photo, limited to 1024x1024px.",
    )
    # Applications Page
    application_ids = fields.Many2many(
        "itm.application",
        "equipment_application_rel",
        "equipment_id",
        "application_id",
        "Applications",
    )

    @api.model
    def _get_type(self):
        if self.env.context.get("search_default_equipment_type"):
            return self.env.context.get("search_default_equipment_type")
        return "bundle"

    # Config Page
    equipment_type = fields.Selection(
        [
            ("bundle", "PHYSICAL"),
            ("virtual", "VIRTUAL"),
            ("product", "PRODUCT"),
            ("other", "OTHER"),
        ],
        "Equipment Type",
        required=True,
        default=_get_type,
    )
    is_contracted = fields.Boolean("Contracted Service")
    is_partitioned = fields.Boolean("Partitions")
    is_backup = fields.Boolean("Backup")
    is_os = fields.Boolean("Operating System")
    is_application = fields.Boolean("Application")
    is_config_file = fields.Boolean("Store Config Files")
    # Config Page - Functions
    function_fileserver = fields.Boolean("File Server")
    function_host = fields.Boolean("Host")
    function_router = fields.Boolean("Router")
    function_database = fields.Boolean("Database Server")
    # Worklogs Page
    worklog_ids = fields.One2many(
        "itm.equipment.worklog",
        "equipment_id",
        "Worklogs on this equipment",
        tracking=True,
    )
    # Contract Page
    contract_partner_id = fields.Many2one("res.partner", "Contractor")
    contract_client_number = fields.Char("Client Nummber")
    contract_owner = fields.Char("Titular")
    contract_nif = fields.Char("NIF")
    contract_direction = fields.Char("Invoice Direction")
    # Virtual Machine Page
    virtual_parent_id = fields.Many2one(
        "itm.equipment", "Virtual Machine", domain="[('function_host','=',1)]"
    )
    virtual_memory_amount = fields.Char("Memory")
    virtual_disk_amount = fields.Char("Disk Size")
    virtual_processor_amount = fields.Char("Number of Processor")
    virtual_network_amount = fields.Char("Number of Network")
    # Partition Page
    partitions_ids = fields.One2many(
        "itm.equipment.partition", "equipment_id", "Partitions on this equipment"
    )
    # Router Page
    router_dmz = fields.Char("DMZ")
    router_forward_ids = fields.One2many(
        "itm.equipment.forward", "equipment_id", "Forward Rules", tracking=True
    )
    router_rules_ids = fields.One2many(
        "itm.equipment.rule",
        "equipment_id",
        "Firewall Rules",
        tracking=True,
    )
    # Network Configuration
    equipment_network_ids = fields.One2many(
        "itm.equipment.network",
        "equipment_id",
        "Network on this equipment",
        tracking=True,
    )
    # Product Page
    product_id = fields.Many2one("product.product", "Product")
    product_serial_number = fields.Char("Serial Number")
    product_warranty = fields.Char("Warranty")
    product_buydate = fields.Date("Buy Date")
    product_note = fields.Text("Product Note")
    # Fileserver Page
    equipment_mapping_ids = fields.One2many(
        "itm.equipment.mapping",
        "equipment_id",
        "Network Shares",
        tracking=True,
    )
    # OS Page
    os_name = fields.Char("OS Name")
    # Services
    ad_service_id = fields.Many2one("itm.service.ad", "Active Directory")
    dhcp_service_id = fields.Many2one("itm.service.dhcp4", "DHCP")
    wireless_service_id = fields.Many2one("itm.service.wireless", "Wireless Service")
    proxy_service_id = fields.Many2one("itm.service.proxy", "Proxy Service")
    vpn_service_id = fields.Many2one("itm.service.vpn", "VPN Service")
    # Database Page
    db_ids = fields.One2many("itm.equipment.db", "equipment_id", "Databases")
    use_proxy = fields.Boolean("Use Proxy")
    proxy_client_config_id = fields.Many2one(
        "itm.equipment.network.proxy", "Proxy Configuration"
    )
    # Store Config File Page
    configuration_file_ids = fields.One2many(
        "itm.equipment.configuration", "equipment_id", "Configuration Files"
    )

    # Log a note on creation of equipment to Site and Equipment chatter.
    #
    @api.model
    def create(self, vals):
        res = super(ItEquipment, self).create(vals)
        mt_note = self.env.ref("mail.mt_note")
        author = self.env.user.partner_id and self.env.user.partner_id.id or False
        msg = _(
            '<div class="o_mail_notification"><ul><li>A new %s was created: \
                <a href="#" class="o_redirect" data-oe-model=itm.equipment data-oe-id="%s"> \
                %s</a></li></ul></div>',
            res._description,
            res.id,
            res.name,
        )
        if res.site_id:
            res.site_id.message_post(body=msg, subtype_id=mt_note.id, author_id=author)
        if res.virtual_parent_id:
            res.virtual_parent_id.message_post(
                body=msg, subtype_id=mt_note.id, author_id=author
            )
        return res

    # Log a note on deletion of credential to Site and Equipment chatter. Since
    # more than one record at a time may be deleted post all deleted records
    # for each site and each equipment together in one post.
    #
    def unlink(self):

        mt_note = self.env.ref("mail.mt_note")
        author = self.env.user.partner_id and self.env.user.partner_id.id or False

        # map access records to sites and equipment
        #
        sites = {}
        equips = {}
        for res in self:
            if res.site_id:
                if res.site_id.id not in sites.keys():
                    sites.update({res.site_id.id: [{"id": res.id, "name": res.name}]})
                else:
                    sites[res.site_id.id].append({"id": res.id, "name": res.name})
            if res.virtual_parent_id:
                if res.virtual_parent_id.id not in equips.keys():
                    equips.update(
                        {res.virtual_parent_id.id: [{"id": res.id, "name": res.name}]}
                    )
                else:
                    equips[res.virtual_parent_id.id].append(
                        {"id": res.id, "name": res.name}
                    )

        Site = self.env["itm.site"]
        for k, v in sites.items():
            msg = ""
            for r in v:
                msg = msg + _(
                    "<li> %s record was deleted: %s</li>", self._description, r["name"]
                )
            note = '<div class="o_mail_notification"><ul>' + msg + "</ul></div>"
            Site.browse(k).message_post(
                body=note, subtype_id=mt_note.id, author_id=author
            )

        Equipment = self.env["itm.equipment"]
        for k, v in equips.items():
            msg = ""
            for r in v:
                msg = msg + _(
                    "<li> %s record was deleted: %s</li>", self._description, r["name"]
                )
            note = '<div class="o_mail_notification"><ul>' + msg + "</ul></div>"
            Equipment.browse(k).message_post(
                body=note, subtype_id=mt_note.id, author_id=author
            )

        return super(ItEquipment, self).unlink()
