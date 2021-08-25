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


from odoo import fields, models


class ItEquipmentNetwork(models.Model):
    _name = "itm.equipment.network"
    _description = "Network Interface"

    equipment_id = fields.Many2one("itm.equipment", "Asset", ondelete="cascade")
    name = fields.Char("Interface Name", required=True)
    mac = fields.Char("MAC Address", required=True)
    network_id = fields.Many2one("itm.site.network", "Network")
    static_ipv4_id = fields.Many2one("itm.site.network.ip4", "Static IPv4 Address")
    use_dhcp4 = fields.Boolean("Use IPv4 DHCP", default=True)
    note = fields.Text()


class ItEquipmentNetworkProxy(models.Model):
    _name = "itm.equipment.network.proxy"
    _description = "Network Proxy Configuration"

    name = fields.Char("Proxy Hostname", required=True)
